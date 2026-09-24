import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import UserSerializer
from apps.notifications.integrations.max.webapp import (
    MaxInitDataError,
    validate_init_data,
)
from apps.notifications.models import MaxWebhookEvent
from apps.notifications.services import get_notification_service


class MaxLaunchView(APIView):
    """Validate MAX launch data and link it only to an authenticated app user."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        init_data = request.data.get('initData') or request.data.get('init_data') or ''
        try:
            # MAX identity linking always requires the signed provider payload,
            # including when local notifications are configured in mock mode.
            launch = validate_init_data(init_data, allow_mock=False)
        except MaxInitDataError:
            return Response(
                {'detail': 'Invalid MAX launch context.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        authenticated = bool(request.user and request.user.is_authenticated)
        user = request.user if authenticated else None
        try:
            with transaction.atomic():
                linked_user = User.objects.select_for_update().filter(
                    max_user_id=launch.max_user_id,
                ).first()

                if authenticated:
                    user = User.objects.select_for_update().get(pk=user.pk)
                    if user.max_user_id and user.max_user_id != launch.max_user_id:
                        return Response(
                            {'detail': 'This account is already linked to a different MAX profile.'},
                            status=status.HTTP_409_CONFLICT,
                        )
                    if linked_user and linked_user.id != user.id:
                        return Response(
                            {'detail': 'This MAX account is already linked to another user.'},
                            status=status.HTTP_409_CONFLICT,
                        )
                elif linked_user:
                    user = linked_user
                else:
                    return Response(
                        {
                            'code': 'account_link_required',
                            'detail': 'Sign in to your UniPath account to link this MAX profile.',
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                changed_fields = []
                if not user.max_user_id:
                    user.max_user_id = launch.max_user_id
                    user.max_linked_at = timezone.now()
                    changed_fields.extend(['max_user_id', 'max_linked_at'])
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
        except IntegrityError:
            # The unique constraint remains the final guard if two accounts
            # race to claim the same MAX identity.
            return Response(
                {'detail': 'This MAX account is already linked to another user.'},
                status=status.HTTP_409_CONFLICT,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
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
        })


class MaxWebhookView(APIView):
    """Receive MAX Bot API webhook updates with secret/idempotency checks."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        if not self._valid_secret(request):
            return Response(
                {'detail': 'Invalid webhook secret.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        payload = request.data if isinstance(request.data, dict) else {}
        event_id = self._event_id(payload)
        event_type = (
            payload.get('update_type')
            or payload.get('event_type')
            or payload.get('type')
            or 'max_update'
        )
        event, created = MaxWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                'event_type': str(event_type),
                'payload': payload,
            },
        )
        if created and str(event_type) == 'bot_started':
            self._send_welcome(payload, event.event_id)

        return Response({
            'ok': True,
            'duplicate': not created,
            'event_id': event.event_id,
        })

    def _send_welcome(self, payload: dict, event_id: str) -> None:
        """Greet a user who just pressed Start and hand them the mini-app button."""
        user = payload.get('user') or {}
        max_user_id = str(user.get('user_id') or user.get('id') or '').strip()
        if not max_user_id:
            return

        client = get_notification_service().get_client()
        client.send_notification(
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
            },
        )

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
