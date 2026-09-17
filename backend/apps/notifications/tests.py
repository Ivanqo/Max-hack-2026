import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.notifications.integrations.max.real_client import RealMaxClient
from apps.notifications.services import NotificationService, get_notification_service
from apps.opportunities.models import Opportunity
from apps.subscriptions.models import Subscription


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
        subscription = Subscription.objects.create(student=student, topic='Backend', active=True)
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
            idempotency_key=f'subscription:{subscription.id}:opportunity:{opportunity.id}',
        ).count(), 1)

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

    def post(self, endpoint, params=None, json=None, headers=None, timeout=None):
        if self.raised:
            raise self.raised
        self.last_headers = headers
        self.last_params = params
        self.last_payload = json
        return self.response


class TestRealMaxClient(TestCase):
    def _client(self, fake):
        class Client(RealMaxClient):
            def _requests(self_inner):
                return fake
        return Client(api_url='https://platform-api2.max.ru', api_key='token')

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


@override_settings(MAX_WEBHOOK_SECRET='secret', MAX_INTEGRATION_MODE='real')
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


@override_settings(
    MAX_BOT_TOKEN='test-token',
    MAX_INTEGRATION_MODE='real',
    MAX_INITDATA_MAX_AGE_SECONDS=86400,
)
class MaxLaunchTest(TestCase):
    def test_valid_init_data_links_max_user_to_local_student(self):
        init_data = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 12345, 'first_name': 'Max', 'last_name': 'Student'}),
            'start_param': 'opportunity_7',
        })

        response = APIClient().post('/api/max/launch/', {'initData': init_data}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['max']['max_user_id'], '12345')
        user = get_user_model().objects.get(max_user_id='12345')
        self.assertEqual(user.role, 'student')
        self.assertFalse(user.is_staff)

    def test_invalid_init_data_is_rejected(self):
        response = APIClient().post(
            '/api/max/launch/',
            {'initData': 'user=%7B%22id%22%3A1%7D&hash=bad'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_nested_webappdata_fragment_is_accepted(self):
        signed = self._signed_init_data({
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': 54321, 'first_name': 'Nested'}),
            'start_param': 'opportunity_99',
        })
        response = APIClient().post(
            '/api/max/launch/',
            {'initData': '#' + urlencode({'WebAppData': signed})},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['max']['max_user_id'], '54321')
        self.assertEqual(response.data['max']['start_param'], 'opportunity_99')

    def test_duplicate_init_data_fields_are_rejected(self):
        response = APIClient().post(
            '/api/max/launch/',
            {'initData': 'user=%7B%22id%22%3A1%7D&user=%7B%22id%22%3A2%7D&hash=bad'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def _signed_init_data(self, params):
        data_check = '\n'.join(f'{key}={value}' for key, value in sorted(params.items()))
        secret = hmac.new(b'WebAppData', b'test-token', hashlib.sha256).digest()
        signature = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        return urlencode({**params, 'hash': signature})
