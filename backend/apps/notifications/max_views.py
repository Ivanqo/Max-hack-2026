import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth import get_user_model
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


class MaxLaunchView(APIView):
    """Validate MAX mini-app launch context and link it to a local student."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        init_data = request.data.get('initData') or request.data.get('init_data') or ''
        try:
            launch = validate_init_data(init_data)
        except MaxInitDataError:
            return Response(
                {'detail': 'Invalid MAX launch context.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        authenticated = bool(request.user and request.user.is_authenticated)
        user = request.user if authenticated else None
        linked_user = User.objects.filter(max_user_id=launch.max_user_id).first()

        if authenticated and linked_user and linked_user.id != user.id:
            return Response(
                {'detail': 'This MAX account is already linked to another user.'},
                status=status.HTTP_409_CONFLICT,
            )

        if linked_user and not authenticated:
            user = linked_user
        elif not user:
            user = self._create_student_for_max(launch)

        user.max_user_id = launch.max_user_id
        user.max_username = launch.username
        user.max_linked_at = timezone.now()
        if launch.first_name and not user.first_name:
            user.first_name = launch.first_name
        if launch.last_name and not user.last_name:
            user.last_name = launch.last_name
        user.save(update_fields=[
            'max_user_id',
            'max_username',
            'max_linked_at',
            'first_name',
            'last_name',
        ])

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

    def _create_student_for_max(self, launch):
        User = get_user_model()
        email = f'max_{launch.max_user_id}@max.local'
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': launch.first_name or 'MAX',
                'last_name': launch.last_name or 'Student',
                'role': 'student',
                'username': launch.username,
                'is_active': True,
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])
        return user


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
        return Response({
            'ok': True,
            'duplicate': not created,
            'event_id': event.event_id,
        })

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
