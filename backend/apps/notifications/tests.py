import hashlib
import hmac
import json
import time
from datetime import timedelta
from io import StringIO
from urllib.parse import urlencode
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.management import call_command
from django.utils import timezone
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.notifications.models import MaxWebhookEvent, Notification
from apps.notifications.integrations.max.real_client import RealMaxClient
from apps.notifications.services import NotificationService, get_notification_service
from apps.opportunities.models import Opportunity
from apps.subscriptions.models import Subscription


@override_settings(USE_MOCK_MAX_CLIENT=True)
class NotificationServiceTest(TestCase):
    def test_subscription_creates_simulated_notification_for_matching_opportunity(self):
        User = get_user_model()
        student = User.objects.create_user(
            email='notify@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        Subscription.objects.create(student=student, topic='Backend', active=True)
        opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='Backend Internship',
            description='Build APIs.',
            requirements='Python',
            verified_status='verified',
            published=True,
        )

        notifications = get_notification_service().create_for_opportunity_subscriptions(opportunity)

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].status, Notification.Status.SIMULATED)

    def test_subscription_notification_is_idempotent(self):
        User = get_user_model()
        student = User.objects.create_user(
            email='dedupe@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        Subscription.objects.create(student=student, topic='Backend', active=True)
        opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='Backend Internship',
            description='Backend APIs.',
            requirements='Python',
            verified_status='verified',
            published=True,
        )

        service = get_notification_service()
        first = service.create_for_opportunity_subscriptions(opportunity)
        second = service.create_for_opportunity_subscriptions(opportunity)

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(Notification.objects.filter(
            idempotency_key=f'student:{student.id}:opportunity:{opportunity.id}',
        ).count(), 1)

    def test_multiple_matching_subscriptions_create_one_notification(self):
        User = get_user_model()
        student = User.objects.create_user(
            email='multi-subscription@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        Subscription.objects.create(student=student, topic='BIM', active=True)
        Subscription.objects.create(student=student, topic='Revit', active=True)
        opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='BIM internship',
            description='Build a model in Revit.',
            requirements='',
            verified_status='verified',
            published=True,
        )

        notifications = get_notification_service().create_for_opportunity_subscriptions(opportunity)

        self.assertEqual(len(notifications), 1)
        self.assertEqual(Notification.objects.filter(student=student, opportunity=opportunity).count(), 1)

    @override_settings(MAX_INTEGRATION_MODE='real', USE_MOCK_MAX_CLIENT=False)
    def test_real_notification_waits_for_max_link_then_sends_once(self):
        student = get_user_model().objects.create_user(
            email='unlinked-notify@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        Subscription.objects.create(student=student, topic='Backend', active=True)
        opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='Backend Internship',
            description='Build Backend APIs.',
            requirements='',
            verified_status='verified',
            published=True,
        )
        client = Mock()
        client.is_available.return_value = True
        client.send_notification.return_value = {'success': True, 'provider': 'max'}
        service = NotificationService(client=client)

        queued, = service.create_for_opportunity_subscriptions(opportunity)
        self.assertEqual(queued.delivery_status, Notification.DeliveryStatus.PENDING)
        client.send_notification.assert_not_called()

        student.max_user_id = 'max-queued-notify'
        student.save(update_fields=['max_user_id'])
        retried, = service.retry_queued_notifications_for_student(student)
        retried.refresh_from_db()

        self.assertEqual(retried.delivery_status, Notification.DeliveryStatus.SENT)
        client.send_notification.assert_called_once()

    @override_settings(MAX_INTEGRATION_MODE='real', USE_MOCK_MAX_CLIENT=False)
    def test_retry_failed_notification_reuses_existing_row(self):
        class RetryClient:
            def is_available(self):
                return True

            def send_notification(self, **kwargs):
                return {
                    'success': True,
                    'message_id': 'retry-message-1',
                    'provider': 'max',
                }

            def get_notification_status(self, message_id):
                return {'status': 'sent'}

        User = get_user_model()
        student = User.objects.create_user(
            email='retry@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
            max_user_id='max-retry-1',
        )
        notification = Notification.objects.create(
            student=student,
            title='Retry me',
            message='Transient delivery failure',
            status=Notification.Status.FAILED,
            delivery_status=Notification.DeliveryStatus.FAILED,
            failed_at=timezone.now(),
            last_error='MAX provider unavailable',
            idempotency_key='retry-key-1',
        )

        result = NotificationService(client=RetryClient()).retry_failed_notifications()

        notification.refresh_from_db()
        self.assertEqual(result, {'total': 1, 'succeeded': 1, 'failed': 0})
        self.assertEqual(Notification.objects.filter(idempotency_key='retry-key-1').count(), 1)
        self.assertEqual(notification.delivery_status, Notification.DeliveryStatus.SENT)
        self.assertEqual(notification.provider_message_id, 'retry-message-1')


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.content = json.dumps(self._payload).encode()

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import exceptions
            raise exceptions.HTTPError(f'status {self.status_code}')


class FakeRequests:
    def __init__(self, response=None, raised=None):
        from requests import exceptions
        self.response = response
        self.raised = raised
        self.exceptions = exceptions
        self.last_headers = None
        self.last_params = None
        self.last_payload = None
        self.last_endpoint = None

    def post(self, endpoint, params=None, json=None, headers=None, timeout=None):
        if self.raised:
            raise self.raised
        self.last_headers = headers
        self.last_endpoint = endpoint
        self.last_params = params
        self.last_payload = json
        return self.response

    def get(self, endpoint, headers=None, timeout=None):
        if self.raised:
            raise self.raised
        self.last_headers = headers
        self.last_endpoint = endpoint
        return self.response


class TestRealMaxClient(TestCase):
    def _client(self, fake):
        class Client(RealMaxClient):
            def _requests(self_inner):
                return fake
        return Client(api_url='https://platform-api2.max.ru', api_key='token')

    @override_settings(MAX_OPEN_APP_TARGET='https://max.ru/unipath_bot')
    def test_real_client_uses_messages_endpoint_and_raw_authorization(self):
        fake = FakeRequests(FakeResponse(200, {'message': {'mid': 'm-1'}}))
        result = self._client(fake).send_notification(
            student_id='local-1',
            title='Title',
            message='Body',
            opportunity_id='42',
            metadata={'max_user_id': 'max-1', 'webapp_payload': 'opportunity_42'},
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'm-1')
        self.assertEqual(fake.last_headers['Authorization'], 'token')
        self.assertEqual(fake.last_params, {'user_id': 'max-1'})
        self.assertEqual(fake.last_payload['attachments'][0]['payload']['buttons'][0][0]['type'], 'open_app')
        self.assertEqual(fake.last_payload['attachments'][0]['payload']['buttons'][0][0]['web_app'], 'https://max.ru/unipath_bot')

    @override_settings(MAX_OPEN_APP_TARGET='https://max.ru/unipath_bot')
    def test_welcome_message_can_open_the_public_mini_app(self):
        fake = FakeRequests(FakeResponse(200, {'message': {'mid': 'welcome-1'}}))
        result = self._client(fake).send_notification(
            student_id='max-bot-welcome',
            title='UniPath MAX',
            message='Открой мини-приложение, чтобы начать.',
            metadata={'max_user_id': 'max-welcome-1', 'webapp_payload': 'home'},
        )

        self.assertTrue(result['success'])
        button = fake.last_payload['attachments'][0]['payload']['buttons'][0][0]
        self.assertEqual(button['type'], 'open_app')
        self.assertEqual(button['payload'], 'home')
        self.assertEqual(button['web_app'], 'https://max.ru/unipath_bot')

    @override_settings(MAX_OPEN_APP_TARGET='http://localhost:3000')
    def test_real_client_omits_open_app_button_without_target(self):
        fake = FakeRequests(FakeResponse(200, {'message': {'mid': 'm-2'}}))
        result = self._client(fake).send_notification(
            student_id='local-1',
            title='Title',
            message='Body',
            opportunity_id='42',
            metadata={'max_user_id': 'max-1', 'webapp_payload': 'opportunity_42'},
        )

        self.assertTrue(result['success'])
        self.assertEqual(fake.last_payload['attachments'], [])

    def test_real_client_maps_provider_error_statuses(self):
        for status_code, expected in [
            (401, 'MAX authorization failed'),
            (429, 'MAX rate limit exceeded'),
            (500, 'MAX provider unavailable'),
        ]:
            fake = FakeRequests(FakeResponse(status_code))
            result = self._client(fake).send_notification(
                student_id='local-1',
                title='Title',
                message='Body',
                metadata={'max_user_id': 'max-1'},
            )
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], expected)

    def test_real_client_timeout_is_sanitized(self):
        from requests import exceptions
        fake = FakeRequests(raised=exceptions.Timeout())
        result = self._client(fake).send_notification(
            student_id='local-1',
            title='Title',
            message='Body',
            metadata={'max_user_id': 'max-1'},
        )
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Request timeout')

    @override_settings(
        MAX_WEBHOOK_URL='https://unipath.example/api/max/webhook/',
        MAX_WEBHOOK_SECRET='webhook-secret',
    )
    def test_webhook_registration_subscribes_to_start_and_message_events(self):
        fake = FakeRequests(FakeResponse(200, {'success': True}))
        result = self._client(fake).ensure_webhook_subscription()

        self.assertTrue(result['success'])
        self.assertEqual(fake.last_endpoint, 'https://platform-api2.max.ru/subscriptions')
        self.assertEqual(
            fake.last_payload['update_types'],
            ['message_created', 'message_callback', 'bot_started'],
        )

    @override_settings(MAX_WEBHOOK_URL='https://unipath.example/api/max/webhook/')
    def test_current_subscription_inspection_returns_provider_data_to_safe_command(self):
        subscriptions = [{
            'url': 'https://unipath.example/api/max/webhook/',
            'update_types': ['message_created', 'bot_started'],
            'secret': 'must-not-be-printed',
        }]
        fake = FakeRequests(FakeResponse(200, subscriptions))
        result = self._client(fake).get_webhook_subscriptions()

        self.assertTrue(result['success'])
        self.assertEqual(fake.last_endpoint, 'https://platform-api2.max.ru/subscriptions')
        self.assertEqual(result['subscriptions'], subscriptions)

    @override_settings(MAX_WEBHOOK_URL='https://unipath.example/api/max/webhook/')
    @patch(
        'apps.notifications.management.commands.inspect_max_webhook.RealMaxClient.get_webhook_subscriptions',
        return_value={
            'success': True,
            'subscriptions': [{
                'url': 'https://unipath.example/api/max/webhook/',
                'update_types': ['message_created', 'bot_started'],
                'secret': 'never-print-this-value',
            }],
        },
    )
    def test_safe_inspection_command_does_not_print_secret_or_full_webhook_url(self, _get_subscriptions):
        output = StringIO()

        call_command('inspect_max_webhook', stdout=output)

        rendered = output.getvalue()
        self.assertIn('Matching subscriptions: 1', rendered)
        self.assertIn('bot_started, message_created', rendered)
        self.assertNotIn('never-print-this-value', rendered)
        self.assertNotIn('https://unipath.example', rendered)


@override_settings(
    MAX_WEBHOOK_SECRET='secret',
    MAX_INTEGRATION_MODE='real',
    MAX_OPEN_APP_TARGET='https://max.ru/unipath_bot',
)
class MaxWebhookTest(TestCase):
    def test_duplicate_webhook_is_idempotent(self):
        client = APIClient()
        payload = {'update_id': 'u-1', 'update_type': 'message_created'}
        first = client.post(
            '/api/max/webhook/',
            payload,
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )
        second = client.post(
            '/api/max/webhook/',
            payload,
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data['duplicate'])
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['duplicate'])

    def test_webhook_rejects_bad_secret(self):
        client = APIClient()
        response = client.post(
            '/api/max/webhook/',
            {'update_id': 'u-2'},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='wrong',
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(MAX_INTEGRATION_MODE='mock')
    @patch('apps.notifications.max_views.get_notification_service')
    def test_mock_provider_is_recorded_as_simulated_instead_of_real_delivery(self, get_service):
        client_adapter = Mock()
        client_adapter.send_notification.return_value = {'success': True, 'provider': 'mock'}
        get_service.return_value.get_client.return_value = client_adapter

        response = APIClient().post(
            '/api/max/webhook/',
            {'update_id': 'mock-start-1', 'update_type': 'bot_started', 'user': {'user_id': 82003}},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(response.status_code, 200)
        claim = MaxWebhookEvent.objects.get(event_type='welcome_claim')
        self.assertEqual(claim.payload['status'], 'simulated')

    @patch('apps.notifications.max_views.get_notification_service')
    def test_mock_result_is_not_reported_as_real_delivery_in_real_mode(self, get_service):
        client_adapter = Mock()
        client_adapter.send_notification.return_value = {'success': True, 'provider': 'mock'}
        get_service.return_value.get_client.return_value = client_adapter

        response = APIClient().post(
            '/api/max/webhook/',
            {'update_id': 'real-mode-mock-start', 'update_type': 'bot_started', 'user': {'user_id': 82005}},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(response.status_code, 200)
        claim = MaxWebhookEvent.objects.get(event_type='welcome_claim')
        self.assertEqual(claim.payload['status'], 'failed')

    @override_settings(MAX_OPEN_APP_TARGET='http://localhost:3000')
    @patch('apps.notifications.max_views.get_notification_service')
    def test_welcome_is_not_sent_without_public_https_open_app_target(self, get_service):
        response = APIClient().post(
            '/api/max/webhook/',
            {'update_id': 'bad-target-start', 'update_type': 'bot_started', 'user': {'user_id': 82004}},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(response.status_code, 200)
        get_service.assert_not_called()
        claim = MaxWebhookEvent.objects.get(event_type='welcome_claim')
        self.assertEqual(claim.payload['status'], 'failed')

    @patch('apps.notifications.max_views.get_notification_service')
    def test_bot_started_sends_welcome_with_open_app_payload_once(self, get_service):
        client_adapter = Mock()
        client_adapter.send_notification.return_value = {'success': True, 'provider': 'max'}
        get_service.return_value.get_client.return_value = client_adapter
        client = APIClient()
        payload = {
            'update_id': 'started-1',
            'update_type': 'bot_started',
            'timestamp': int(time.time() * 1000),
            'chat_id': 12345,
            'user': {'user_id': 12345, 'first_name': 'Student'},
        }

        first = client.post(
            '/api/max/webhook/', payload, format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )
        duplicate = client.post(
            '/api/max/webhook/', payload, format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data['duplicate'])
        self.assertTrue(duplicate.data['duplicate'])
        client_adapter.send_notification.assert_called_once()
        kwargs = client_adapter.send_notification.call_args.kwargs
        self.assertEqual(kwargs['metadata']['max_user_id'], '12345')
        self.assertEqual(kwargs['metadata']['webapp_payload'], 'home')
        self.assertIn('Открой мини-приложение', kwargs['message'])
        self.assertFalse(get_user_model().objects.filter(max_user_id='12345').exists())

    @patch('apps.notifications.max_views.get_notification_service')
    def test_message_created_start_command_greets_and_deduplicates_bot_started(self, get_service):
        client_adapter = Mock()
        client_adapter.send_notification.return_value = {'success': True, 'provider': 'max'}
        get_service.return_value.get_client.return_value = client_adapter
        client = APIClient()
        started = {
            'update_id': 'start-event-1',
            'update_type': 'bot_started',
            'user': {'user_id': 82001},
        }
        command = {
            'update_id': 'start-event-2',
            'update_type': 'message_created',
            'message': {
                'sender': {'user_id': 82001},
                'body': {'text': '/start'},
            },
        }

        first = client.post('/api/max/webhook/', started, format='json', HTTP_X_MAX_BOT_API_SECRET='secret')
        second = client.post('/api/max/webhook/', command, format='json', HTTP_X_MAX_BOT_API_SECRET='secret')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        client_adapter.send_notification.assert_called_once()
        self.assertEqual(client_adapter.send_notification.call_args.kwargs['metadata']['webapp_payload'], 'home')

    @patch('apps.notifications.max_views.get_notification_service')
    def test_a_later_explicit_start_gets_a_new_welcome(self, get_service):
        client_adapter = Mock()
        client_adapter.send_notification.return_value = {'success': True, 'provider': 'max'}
        get_service.return_value.get_client.return_value = client_adapter
        client = APIClient()
        first = client.post(
            '/api/max/webhook/',
            {'update_id': 'later-start-1', 'update_type': 'bot_started', 'user': {'user_id': 82008}},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )
        claim = MaxWebhookEvent.objects.get(event_type='welcome_claim')
        claim.processed_at = timezone.now() - timedelta(minutes=2)
        claim.save(update_fields=['processed_at'])
        second = client.post(
            '/api/max/webhook/',
            {
                'update_id': 'later-start-2',
                'update_type': 'message_created',
                'message': {'sender': {'user_id': 82008}, 'body': {'text': '/start'}},
            },
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(client_adapter.send_notification.call_count, 2)

    @patch('apps.notifications.max_views.get_notification_service')
    def test_message_created_non_start_does_not_greet(self, get_service):
        response = APIClient().post(
            '/api/max/webhook/',
            {
                'update_id': 'chat-message-1',
                'update_type': 'message_created',
                'message': {'sender': {'user_id': 82002}, 'body': {'text': 'hello'}},
            },
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(response.status_code, 200)
        get_service.assert_not_called()

    @patch('apps.notifications.max_views.get_notification_service')
    def test_non_start_event_does_not_send_welcome(self, get_service):
        response = APIClient().post(
            '/api/max/webhook/',
            {'update_id': 'message-1', 'update_type': 'message_created', 'user': {'user_id': 9}},
            format='json',
            HTTP_X_MAX_BOT_API_SECRET='secret',
        )

        self.assertEqual(response.status_code, 200)
        get_service.assert_not_called()


@override_settings(
    MAX_BOT_TOKEN='test-token',
    MAX_INTEGRATION_MODE='real',
    MAX_INITDATA_MAX_AGE_SECONDS=86400,
)
class MaxLaunchTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            email='mai-student@test.local', password='pass12345',
            role='student', university='МАИ',
        )
        self.admin = User.objects.create_user(
            email='mgsu-admin@test.local', password='pass12345',
            role='admin', university='НИУ МГСУ',
        )

    def _launch_as(self, user, init_data):
        client = APIClient()
        client.force_authenticate(user=user)
        return client.post('/api/max/launch/', {'initData': init_data}, format='json')

    def test_valid_init_data_links_max_profile_to_existing_student(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12345, 'first_name': 'Max', 'last_name': 'Student'}),
            'start_param': 'opportunity_7',
        })

        response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['max']['max_user_id'], '12345')
        self.assertEqual(response.data['user']['id'], self.student.id)
        self.assertEqual(response.data['user']['role'], 'student')
        self.student.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12345')
        self.assertEqual(get_user_model().objects.filter(max_user_id='12345').count(), 1)

    def test_valid_init_data_links_max_profile_to_existing_admin(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 54321, 'first_name': 'Max', 'last_name': 'Admin'}),
        })

        response = self._launch_as(self.admin, init_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.admin.id)
        self.assertEqual(response.data['user']['role'], 'admin')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.max_user_id, '54321')

    @patch('apps.notifications.max_views.get_notification_service')
    def test_successful_student_link_retries_queued_notifications(self, get_service):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 54322}),
        })

        response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 200)
        get_service.return_value.retry_queued_notifications_for_student.assert_called_once()
        linked_student = get_service.return_value.retry_queued_notifications_for_student.call_args.args[0]
        self.assertEqual(linked_student.pk, self.student.pk)

    def test_unlinked_anonymous_launch_requires_existing_account(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12346}),
        })

        response = APIClient().post('/api/max/launch/', {'initData': init_data}, format='json')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['code'], 'account_link_required')
        self.assertFalse(get_user_model().objects.filter(max_user_id='12346').exists())

    def test_signed_authenticated_launch_moves_link_from_mgsu_to_mai(self):
        editor = get_user_model().objects.create_user(
            email='editor@test.local', password='pass12345', role='editor',
            university='МАИ', max_user_id='12356',
        )
        other_student = get_user_model().objects.create_user(
            email='other-student@test.local', password='pass12345', role='student',
            university='НИУ МГСУ', max_user_id='12357',
        )
        self.admin.max_user_id = '12347'
        self.admin.save(update_fields=['max_user_id'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12347}),
        })
        first = self._launch_as(self.admin, init_data)
        second = self._launch_as(self.student, init_data)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.admin.refresh_from_db()
        self.assertIsNone(self.admin.max_user_id)
        self.assertEqual(self.admin.max_username, '')
        self.assertIsNone(self.admin.max_linked_at)
        self.student.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12347')
        self.assertEqual(second.data['user']['role'], 'student')
        self.assertEqual(get_user_model().objects.filter(max_user_id='12347').count(), 1)
        editor.refresh_from_db()
        other_student.refresh_from_db()
        self.assertEqual(editor.max_user_id, '12356')
        self.assertEqual(editor.role, 'editor')
        self.assertEqual(other_student.max_user_id, '12357')
        self.assertEqual(other_student.role, 'student')

    def test_admin_launch_does_not_take_max_link_from_student(self):
        self.student.max_user_id = '12358'
        self.student.max_linked_at = timezone.now()
        self.student.save(update_fields=['max_user_id', 'max_linked_at'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12358}),
        })

        response = self._launch_as(self.admin, init_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.admin.id)
        self.assertEqual(response.data['user']['role'], 'admin')
        self.student.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12358')
        self.assertIsNone(self.admin.max_user_id)
        self.assertEqual(get_user_model().objects.filter(max_user_id='12358').count(), 1)

    def test_opportunity_deep_link_restores_linked_student_session_from_admin(self):
        self.student.max_user_id = '12359'
        self.student.max_linked_at = timezone.now()
        self.student.save(update_fields=['max_user_id', 'max_linked_at'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12359}),
            'start_param': 'opportunity_33',
        })

        response = self._launch_as(self.admin, init_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.student.id)
        self.assertEqual(response.data['user']['role'], 'student')
        self.assertEqual(response.data['max']['start_param'], 'opportunity_33')
        self.student.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12359')
        self.assertIsNone(self.admin.max_user_id)

    def test_repeat_launch_for_same_account_is_idempotent(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12350}),
        })
        first = self._launch_as(self.student, init_data)
        self.student.refresh_from_db()
        linked_at = self.student.max_linked_at
        second = self._launch_as(self.student, init_data)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12350')
        self.assertEqual(self.student.max_linked_at, linked_at)

    def test_anonymous_launch_does_not_move_profile_from_old_account(self):
        self.admin.max_user_id = '12351'
        self.admin.max_username = 'old-profile'
        self.admin.max_linked_at = timezone.now()
        self.admin.save(update_fields=['max_user_id', 'max_username', 'max_linked_at'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12351}),
        })

        response = APIClient().post('/api/max/launch/', {'initData': init_data}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.admin.id)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.max_user_id, '12351')
        self.student.refresh_from_db()
        self.assertIsNone(self.student.max_user_id)

    def test_existing_account_link_cannot_be_silently_replaced(self):
        self.student.max_user_id = '12348'
        self.student.save(update_fields=['max_user_id'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12349}),
        })

        response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 409)
        self.student.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12348')

    def test_target_account_with_another_max_profile_rejects_transfer(self):
        self.admin.max_user_id = '12352'
        self.admin.save(update_fields=['max_user_id'])
        self.student.max_user_id = '12353'
        self.student.save(update_fields=['max_user_id'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12352}),
        })

        response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 409)
        self.student.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.student.max_user_id, '12353')
        self.assertEqual(self.admin.max_user_id, '12352')

    def test_integrity_race_rolls_back_old_account_unlink(self):
        User = get_user_model()
        original_save = User.save
        self.admin.max_user_id = '12354'
        self.admin.save(update_fields=['max_user_id'])
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12354}),
        })

        def simulate_unique_constraint_race(instance, *args, **kwargs):
            if instance.pk == self.student.pk and 'max_user_id' in kwargs.get('update_fields', []):
                raise IntegrityError('unique constraint race')
            return original_save(instance, *args, **kwargs)

        with patch.object(User, 'save', autospec=True, side_effect=simulate_unique_constraint_race):
            response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 409)
        self.admin.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.admin.max_user_id, '12354')
        self.assertIsNone(self.student.max_user_id)

    def test_link_log_has_correlation_id_without_account_identifiers(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 987654321012345}),
        })

        with self.assertLogs('apps.notifications.max_views', level='INFO') as captured:
            response = self._launch_as(self.student, init_data)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response['X-Correlation-ID'], r'^[a-f0-9]{32}$')
        log_text = '\n'.join(captured.output)
        self.assertIn(response['X-Correlation-ID'], log_text)
        self.assertNotIn('987654321012345', log_text)
        self.assertNotIn('initData', log_text)

    def test_invalid_init_data_is_rejected(self):
        response = self._launch_as(self.student, 'user=%7B%22id%22%3A1%7D&hash=bad')
        self.assertEqual(response.status_code, 400)

    def test_unsigned_init_data_is_rejected(self):
        response = self._launch_as(
            self.student,
            urlencode({'auth_date': str(int(time.time())), 'user': json.dumps({'id': 12355})}),
        )
        self.assertEqual(response.status_code, 400)

    def test_nested_webappdata_fragment_is_accepted(self):
        signed = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 54321, 'first_name': 'Nested'}),
            'start_param': 'opportunity_99',
        })
        response = self._launch_as(self.student, '#' + urlencode({'WebAppData': signed}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['max']['max_user_id'], '54321')
        self.assertEqual(response.data['max']['start_param'], 'opportunity_99')

    def test_duplicate_outer_webappdata_fields_are_rejected(self):
        signed = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 11111, 'first_name': 'Duplicate'}),
        })
        response = self._launch_as(
            self.student,
            '#' + urlencode({'WebAppData': signed}) + '&' + urlencode({'WebAppData': signed}),
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_init_data_fields_are_rejected(self):
        response = self._launch_as(
            self.student,
            'user=%7B%22id%22%3A1%7D&user=%7B%22id%22%3A2%7D&hash=bad',
        )
        self.assertEqual(response.status_code, 400)

    def _signed_init_data(self, params):
        data_check = '\n'.join(f'{key}={value}' for key, value in sorted(params.items()))
        secret = hmac.new(b'WebAppData', b'test-token', hashlib.sha256).digest()
        signature = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        return urlencode({**params, 'hash': signature})


@override_settings(MAX_INTEGRATION_MODE='mock')
class MaxLaunchMockModeSecurityTest(TestCase):
    def test_unsigned_mock_launch_data_cannot_link_an_account(self):
        user = get_user_model().objects.create_user(
            email='mock-mode@test.local', password='pass12345', role='student',
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/max/launch/', {'initData': 'mock:998877'}, format='json')

        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertIsNone(user.max_user_id)
