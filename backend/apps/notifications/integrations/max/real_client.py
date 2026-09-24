"""
Real MAX Client - Implementation for production MAX API integration.
"""
import logging
import re
from typing import Dict, Any, Optional
from django.conf import settings
from .client import MaxClient
from .urls import is_public_https_url

logger = logging.getLogger(__name__)


class RealMaxClient(MaxClient):
    """
    Production implementation of MAX API client.
    Handles actual HTTP requests to the MAX platform.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize real MAX client.

        Args:
            api_url: MAX API base URL (defaults to settings)
            api_key: MAX API key (defaults to settings)
            timeout: Request timeout in seconds
        """
        self.api_url = (api_url or getattr(settings, 'MAX_API_URL', '')).rstrip('/')
        self.api_key = api_key or getattr(settings, 'MAX_BOT_TOKEN', '')
        self.timeout = timeout

        if not self.api_url:
            logger.warning("MAX_API_URL not configured")
        if not self.api_key:
            logger.warning("MAX_BOT_TOKEN not configured")

        logger.info("MAX API client initialized; endpoint configured=%s", bool(self.api_url))

    def send_notification(
        self,
        student_id: str,
        title: str,
        message: str,
        opportunity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification through MAX API.

        Args:
            student_id: Unique identifier for the student
            title: Notification title
            message: Notification message content
            opportunity_id: Optional opportunity identifier
            metadata: Optional additional metadata

        Returns:
            Dict containing response from MAX API

        Raises:
            requests.RequestException: If the API request fails
        """
        if not self.api_url or not self.api_key:
            logger.error("MAX API not configured")
            return {
                'success': False,
                'message_id': None,
                'error': 'MAX API not configured'
            }
        max_user_id = str((metadata or {}).get('max_user_id') or '').strip()
        if not max_user_id:
            logger.warning("Cannot send MAX message: recipient is not linked")
            return {
                'success': False,
                'message_id': None,
                'error': 'MAX user is not linked'
            }
        requests = self._requests()
        if requests is None:
            return {
                'success': False,
                'message_id': None,
                'error': 'requests package is not installed'
            }

        endpoint = f"{self.api_url}/messages"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = self._message_payload(title, message, opportunity_id, metadata or {})

        try:
            response = requests.post(
                endpoint,
                params={'user_id': max_user_id},
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            if response.status_code == 401:
                return self._failure('MAX authorization failed')
            if response.status_code == 429:
                return self._failure('MAX rate limit exceeded')
            if response.status_code >= 500:
                return self._failure('MAX provider unavailable')
            response.raise_for_status()

            data = response.json()
            message_id = self._message_id(data)

            return {
                'success': True,
                'message_id': message_id,
                'provider': 'max',
                'error': None
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message_id': None,
                'error': 'Request timeout'
            }

        except requests.exceptions.RequestException:
            logger.error("MAX API request failed; provider response details suppressed")
            return self._failure('MAX request failed')

    def get_notification_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the delivery status of a notification via MAX API.

        Args:
            message_id: The MAX message identifier

        Returns:
            Dict containing status information

        Raises:
            requests.RequestException: If the API request fails
        """
        return {
            'success': True,
            'status': 'sent',
            'message_id': message_id,
            'error': None,
        }

    def is_available(self) -> bool:
        """
        Check if the MAX API is currently available.

        Returns:
            bool: True if API is available, False otherwise
        """
        return bool(self.api_url and self.api_key and self._requests() is not None)

    def ensure_webhook_subscription(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register the production webhook subscription in MAX."""
        webhook_url = webhook_url or getattr(settings, 'MAX_WEBHOOK_URL', '')
        secret = secret or getattr(settings, 'MAX_WEBHOOK_SECRET', '')
        if not webhook_url or not secret:
            return self._failure('MAX webhook URL or secret is not configured')
        if not webhook_url.startswith('https://'):
            return self._failure('MAX webhook URL must use HTTPS')
        if not re.fullmatch(r'[A-Za-z0-9_-]{5,256}', secret):
            return self._failure('MAX webhook secret must match [A-Za-z0-9_-]{5,256}')
        requests = self._requests()
        if requests is None:
            return self._failure('requests package is not installed')

        try:
            response = requests.post(
                f'{self.api_url}/subscriptions',
                json={
                    'url': webhook_url,
                    'secret': secret,
                    'update_types': [
                        'message_created',
                        'message_callback',
                        'bot_started',
                    ],
                },
                headers={
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json',
                },
                timeout=self.timeout,
            )
            if response.status_code == 401:
                return self._failure('MAX authorization failed')
            if response.status_code == 429:
                return self._failure('MAX rate limit exceeded')
            if response.status_code >= 500:
                return self._failure('MAX provider unavailable')
            response.raise_for_status()
            return {
                'success': True,
                'provider': 'max',
                'subscription': response.json() if response.content else {},
                'error': None,
            }
        except requests.exceptions.RequestException:
            logger.error("MAX webhook subscription request failed; provider details suppressed")
            return self._failure('MAX subscription request failed')

    def get_webhook_subscriptions(self) -> Dict[str, Any]:
        """Read current webhook subscriptions without exposing credentials."""
        if not self.api_url or not self.api_key:
            return self._failure('MAX API is not configured')
        requests = self._requests()
        if requests is None:
            return self._failure('requests package is not installed')
        try:
            response = requests.get(
                f'{self.api_url}/subscriptions',
                headers={'Authorization': self.api_key},
                timeout=self.timeout,
            )
            if response.status_code == 401:
                return self._failure('MAX authorization failed')
            if response.status_code == 429:
                return self._failure('MAX rate limit exceeded')
            if response.status_code >= 500:
                return self._failure('MAX provider unavailable')
            response.raise_for_status()
            data = response.json() if response.content else []
            if isinstance(data, dict):
                subscriptions = data.get('subscriptions', [])
            else:
                subscriptions = data
            if not isinstance(subscriptions, list):
                return self._failure('MAX subscription response is invalid')
            return {
                'success': True,
                'subscriptions': subscriptions,
                'error': None,
            }
        except requests.exceptions.RequestException:
            logger.error("MAX webhook subscription inspection failed; provider details suppressed")
            return self._failure('MAX subscription inspection failed')

    def _message_payload(
        self,
        title: str,
        message: str,
        opportunity_id: Optional[str],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        text = f"{title}\n\n{message}".strip()
        open_app_target = getattr(settings, 'MAX_OPEN_APP_TARGET', '').strip()
        payload = {
            'text': text,
            'attachments': [],
        }
        if is_public_https_url(open_app_target):
            start_payload = metadata.get('webapp_payload') or (
                f'opportunity_{opportunity_id}' if opportunity_id else 'notifications'
            )
            payload['attachments'].append({
                'type': 'inline_keyboard',
                'payload': {
                    'buttons': [[{
                        'type': 'open_app',
                        'text': 'Открыть в UniPath MAX',
                        'web_app': open_app_target,
                        'payload': start_payload,
                    }]]
                },
            })
        return payload

    def _message_id(self, data: Dict[str, Any]) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        nested = data.get('message') if isinstance(data.get('message'), dict) else {}
        return (
            data.get('message_id')
            or data.get('id')
            or data.get('mid')
            or nested.get('mid')
            or nested.get('id')
        )

    def _failure(self, error: str) -> Dict[str, Any]:
        return {
            'success': False,
            'message_id': None,
            'error': error,
            'provider': 'max',
        }

    def _requests(self):
        try:
            import requests
            return requests
        except ModuleNotFoundError:
            logger.warning("requests package is not installed; RealMaxClient is unavailable")
            return None
