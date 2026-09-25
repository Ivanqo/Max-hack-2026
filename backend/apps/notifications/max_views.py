import hashlib
import hmac
import json
import logging
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import UserSerializer
from apps.notifications.integrations.max.observability import (
    log_max_event,
    new_correlation_id,
)
from apps.notifications.integrations.max.urls import is_public_https_url
from apps.notifications.integrations.max.webapp import (
    MaxInitDataError,
    validate_init_data,
)
from apps.notifications.models import MaxWebhookEvent
from apps.notifications.services import get_notification_service

logger = logging.getLogger(__name__)


class _RetryLink(Exception):
    """A MAX link changed while its owner and target rows were being locked."""


class MaxLaunchView(APIView):
    """Validate signed MAX launch data and link it to the authenticated account."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        correlation_id = new_correlation_id()
        log_max_event(logger, 'max_launch_received', correlation_id, stage='received')
        init_data = request.data.get('initData') or request.data.get('init_data') or ''
        try:
            # MAX identity linking always requires the signed provider payload,
            # including when local notifications are configured in mock mode.
            launch = validate_init_data(init_data, allow_mock=False)
        except MaxInitDataError:
            log_max_event(
                logger,
                'max_signature_validation',
                correlation_id,
                result='failed',
                stage='validation',
            )
            return self._response(
                {'detail': 'Invalid MAX launch context.'},
                status.HTTP_400_BAD_REQUEST,
                correlation_id,
            )

        log_max_event(
            logger,
            'max_signature_validation',
            correlation_id,
            result='succeeded',
            stage='validation',
        )

        User = get_user_model()
        authenticated = bool(request.user and request.user.is_authenticated)
        target_id = request.user.pk if authenticated else None
        link_result = None
        user = None
        try:
            # Lock the linked owner and destination in primary-key order. If a
            # concurrent link changed the owner before both locks were held,
            # retry with the new owner. The unique DB constraint handles the
            # no-owner-yet race where there is no row to lock.
            for _attempt in range(4):
                source_id = User.objects.filter(
                    max_user_id=launch.max_user_id,
                ).values_list('pk', flat=True).first()
                lock_ids = sorted({pk for pk in (target_id, source_id) if pk is not None})
                try:
                    with transaction.atomic():
                        locked_users = list(
                            User.objects.select_for_update()
                            .filter(pk__in=lock_ids)
                            .order_by('pk')
                        )
                        users_by_id = {row.pk: row for row in locked_users}
                        current_source_id = User.objects.filter(
                            max_user_id=launch.max_user_id,
                        ).values_list('pk', flat=True).first()
                        if current_source_id is not None and current_source_id not in lock_ids:
                            raise _RetryLink

                        linked_user = users_by_id.get(current_source_id)
                        if authenticated:
                            user = users_by_id.get(target_id)
                            if user is None:
                                raise User.DoesNotExist
                            if user.max_user_id and user.max_user_id != launch.max_user_id:
                                return self._rejected(
                                    correlation_id,
                                    'This account is already linked to a different MAX profile.',
                                )
                            if linked_user and linked_user.pk != user.pk:
                                # Moving a profile is permitted only from an
                                # authenticated target account and signed data.
                                linked_user.max_user_id = None
                                linked_user.max_username = ''
                                linked_user.max_linked_at = None
                                linked_user.save(update_fields=[
                                    'max_user_id',
                                    'max_username',
                                    'max_linked_at',
                                ])
                                link_result = 'moved'
                        elif linked_user:
                            user = linked_user
                        else:
                            return self._response(
                                {
                                    'code': 'account_link_required',
                                    'detail': 'Sign in to your UniPath account to link this MAX profile.',
                                },
                                status.HTTP_401_UNAUTHORIZED,
                                correlation_id,
                            )

                        changed_fields = []
                        if not user.max_user_id:
                            user.max_user_id = launch.max_user_id
                            user.max_linked_at = timezone.now()
                            changed_fields.extend(['max_user_id', 'max_linked_at'])
                            if link_result != 'moved':
                                link_result = 'created'
                        if launch.username and user.max_username != launch.username:
                            user.max_username = launch.username
                            changed_fields.append('max_username')
                        if launch.first_name and not user.first_name:
                            user.first_name = launch.first_name
                            changed_fields.append('first_name')
                        if launch.last_name and not user.last_name:
                            user.last_name = launch.last_name
                            changed_fields.append('last_name')
                        if changed_fields:
                            user.save(update_fields=changed_fields)
                        if link_result is None:
                            link_result = 'unchanged'
                    break
                except _RetryLink:
                    continue
            else:
                raise IntegrityError('MAX profile link changed repeatedly')
        except IntegrityError:
            log_max_event(
                logger,
                'max_link',
                correlation_id,
                result='rejected',
                stage='link',
            )
            return self._response(
                {'detail': 'This MAX account is already linked or being linked to another user.'},
                status.HTTP_409_CONFLICT,
                correlation_id,
            )

        log_max_event(
            logger,
            'max_link',
            correlation_id,
            result=link_result or 'unchanged',
            role=user.role,
            stage='link',
        )
        refresh = RefreshToken.for_user(user)
        return self._response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'max': {
                'max_user_id': launch.max_user_id,
                'username': launch.username,
                'start_param': launch.start_param,
            },
        }, status.HTTP_200_OK, correlation_id)

    def _rejected(self, correlation_id: str, detail: str) -> Response:
        log_max_event(
            logger,
            'max_link',
            correlation_id,
            result='rejected',
            stage='link',
        )
        return self._response({'detail': detail}, status.HTTP_409_CONFLICT, correlation_id)

    @staticmethod
    def _response(data, http_status, correlation_id):
        response = Response(data, status=http_status)
        response['X-Correlation-ID'] = correlation_id
        return response


class MaxWebhookView(APIView):
    """Receive MAX Bot API webhook updates with secret/idempotency checks."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        correlation_id = new_correlation_id()
        payload = request.data if isinstance(request.data, dict) else {}
        event_type = self._event_type(payload)
        if not self._valid_secret(request):
            log_max_event(
                logger,
                'max_webhook_received',
                correlation_id,
                result='rejected',
                stage='secret_validation',
                update_type=event_type,
            )
            return self._response(
                {'detail': 'Invalid webhook secret.'},
                status.HTTP_403_FORBIDDEN,
                correlation_id,
            )

        log_max_event(
            logger,
            'max_webhook_received',
            correlation_id,
            result='accepted',
            stage='received',
            update_type=event_type,
        )
        event_id = self._event_id(payload)
        event, created = MaxWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': payload,
            },
        )

        if self._is_start_event(event_type, payload):
            self._send_welcome_once(payload, event.event_id, correlation_id)

        return self._response({
            'ok': True,
            'duplicate': not created,
        }, status.HTTP_200_OK, correlation_id)

    def _send_welcome_once(self, payload: dict, event_id: str, correlation_id: str) -> None:
        user = self._event_user(payload)
        max_user_id = str(user.get('user_id') or user.get('id') or '').strip()
        if not max_user_id:
            log_max_event(
                logger,
                'max_welcome',
                correlation_id,
                result='not_sent',
                stage='missing_recipient',
            )
            return

        # The database key is a one-way digest; no MAX identity is retained in
        # the welcome deduplication record or in logs.
        claim_id = 'welcome:' + hashlib.sha256(max_user_id.encode()).hexdigest()
        with transaction.atomic():
            claim, created = MaxWebhookEvent.objects.get_or_create(
                event_id=claim_id,
                defaults={
                    'event_type': 'welcome_claim',
                    'payload': {'status': 'sending'},
                },
            )
            if not created:
                claim = MaxWebhookEvent.objects.select_for_update().get(pk=claim.pk)
                claim_status = (claim.payload or {}).get('status')
                dedupe_seconds = max(0, int(getattr(settings, 'MAX_WELCOME_DEDUPE_SECONDS', 60)))
                dedupe_after = timezone.now() - timedelta(seconds=dedupe_seconds)
                recent_start = claim.processed_at >= dedupe_after
                if recent_start and claim_status in {'sending', 'sent', 'simulated'}:
                    log_max_event(
                        logger,
                        'max_welcome',
                        correlation_id,
                        result='not_sent',
                        stage='duplicate_start',
                    )
                    return
                claim.payload = {'status': 'sending'}
                claim.processed_at = timezone.now()
                claim.save(update_fields=['payload', 'processed_at'])

        mode = getattr(settings, 'MAX_INTEGRATION_MODE', 'mock')
        if not is_public_https_url(getattr(settings, 'MAX_OPEN_APP_TARGET', '')):
            with transaction.atomic():
                claim = MaxWebhookEvent.objects.select_for_update().get(event_id=claim_id)
                claim.payload = {'status': 'failed'}
                claim.save(update_fields=['payload'])
            log_max_event(
                logger,
                'max_welcome',
                correlation_id,
                mode=mode,
                result='not_sent',
                stage='open_app_configuration',
            )
            return
        try:
            result = get_notification_service().get_client().send_notification(
                student_id='max-bot-welcome',
                title='UniPath MAX',
                message=(
                    'Привет! UniPath MAX поможет собрать карьерный профиль, '
                    'построить карьерный маршрут и найти подходящие стажировки и практики. '
                    'Открой мини-приложение, чтобы начать.'
                ),
                metadata={
                    'max_user_id': max_user_id,
                    'webapp_payload': 'home',
                    'webhook_event_id': event_id,
                    'correlation_id': correlation_id,
                },
            )
            returned_provider = result.get('provider') if isinstance(result, dict) else None
            provider = 'mock' if mode != 'real' or returned_provider == 'mock' else (
                'max' if returned_provider == 'max' else 'unknown'
            )
            sent = bool(isinstance(result, dict) and result.get('success'))
            if mode == 'real' and provider != 'max':
                sent = False
        except Exception:
            sent = False
            provider = 'max' if mode == 'real' else 'mock'

        claim_status = ('simulated' if provider == 'mock' or mode != 'real' else 'sent') if sent else 'failed'
        with transaction.atomic():
            claim = MaxWebhookEvent.objects.select_for_update().get(event_id=claim_id)
            claim.payload = {'status': claim_status}
            claim.save(update_fields=['payload'])

        log_max_event(
            logger,
            'max_welcome',
            correlation_id,
            mode=mode,
            provider=provider,
            result=claim_status,
            stage='delivery',
        )

    @staticmethod
    def _event_user(payload: dict) -> dict:
        user = payload.get('user')
        if isinstance(user, dict):
            return user
        message = payload.get('message')
        if isinstance(message, dict):
            sender = message.get('sender')
            if isinstance(sender, dict):
                return sender
        return {}

    @classmethod
    def _is_start_event(cls, event_type: str, payload: dict) -> bool:
        if event_type == 'bot_started':
            return True
        if event_type != 'message_created':
            return False
        message = payload.get('message')
        body = message.get('body') if isinstance(message, dict) else None
        command = body.get('text') if isinstance(body, dict) else None
        return bool(re.match(r'^\s*/start(?:@[A-Za-z0-9_]+)?(?:\s|$)', str(command or ''), re.IGNORECASE))

    @staticmethod
    def _event_type(payload: dict) -> str:
        value = payload.get('update_type') or payload.get('event_type') or payload.get('type') or 'max_update'
        value = str(value)
        return value[:100] if re.fullmatch(r'[A-Za-z0-9_-]{1,100}', value) else 'unknown'

    def _valid_secret(self, request) -> bool:
        expected = getattr(settings, 'MAX_WEBHOOK_SECRET', '')
        mode = getattr(settings, 'MAX_INTEGRATION_MODE', 'mock')
        if not expected and mode != 'real':
            return True
        supplied = request.headers.get('X-Max-Bot-Api-Secret', '')
        return bool(expected) and hmac.compare_digest(supplied, expected)

    def _event_id(self, payload: dict) -> str:
        for key in ['update_id', 'event_id', 'id']:
            if payload.get(key):
                return str(payload[key])
        message = payload.get('message') or {}
        if isinstance(message, dict):
            for key in ['mid', 'id']:
                if message.get(key):
                    return f'message:{message[key]}'
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
        return f'sha256:{hashlib.sha256(raw).hexdigest()}'

    @staticmethod
    def _response(data, http_status, correlation_id):
        response = Response(data, status=http_status)
        response['X-Correlation-ID'] = correlation_id
        return response
