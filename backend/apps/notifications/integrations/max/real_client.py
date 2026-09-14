"""
Real MAX Client - Implementation for production MAX API integration.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .client import MaxClient

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
        self.api_url = api_url or getattr(settings, 'MAX_API_URL', '')
        self.api_key = api_key or getattr(settings, 'MAX_BOT_TOKEN', '')
        self.timeout = timeout

        if not self.api_url:
            logger.warning("MAX_API_URL not configured")
        if not self.api_key:
            logger.warning("MAX_API_KEY not configured")

        logger.info(f"RealMaxClient initialized with URL: {self.api_url}")

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
        requests = self._requests()
        if requests is None:
            return {
                'success': False,
                'message_id': None,
                'error': 'requests package is not installed'
            }

        endpoint = f"{self.api_url}/notifications/send"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'student_id': student_id,
            'title': title,
            'message': message,
            'opportunity_id': opportunity_id,
            'metadata': metadata or {}
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            message_id = data.get('message_id', data.get('id'))

            logger.info(
                f"Notification sent via MAX - ID: {message_id}, "
                f"Student: {student_id}, Title: {title}"
            )

            return {
                'success': True,
                'message_id': message_id,
                'provider': 'max',
                'error': None
            }

        except requests.exceptions.Timeout:
            logger.error(f"MAX API timeout for student {student_id}")
            return {
                'success': False,
                'message_id': None,
                'error': 'Request timeout'
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"MAX API error for student {student_id}: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

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
        if not self.api_url or not self.api_key:
            logger.error("MAX API not configured")
            return {
                'success': False,
                'status': 'unknown',
                'error': 'MAX API not configured'
            }
        requests = self._requests()
        if requests is None:
            return {
                'success': False,
                'status': 'unknown',
                'error': 'requests package is not installed'
            }

        endpoint = f"{self.api_url}/notifications/{message_id}/status"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'status': data.get('status', 'unknown'),
                'message_id': message_id,
                'error': None
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"MAX API status check error for {message_id}: {str(e)}")
            return {
                'success': False,
                'status': 'unknown',
                'error': str(e)
            }

    def is_available(self) -> bool:
        """
        Check if the MAX API is currently available.

        Returns:
            bool: True if API is available, False otherwise
        """
        if not self.api_url or not self.api_key:
            return False
        requests = self._requests()
        if requests is None:
            return False

        endpoint = f"{self.api_url}/health"
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=5
            )
            is_available = response.status_code == 200

            if not is_available:
                logger.warning(f"MAX API health check failed: {response.status_code}")

            return is_available

        except requests.exceptions.RequestException as e:
            logger.warning(f"MAX API health check failed: {str(e)}")
            return False

    def _requests(self):
        try:
            import requests
            return requests
        except ModuleNotFoundError:
            logger.warning("requests package is not installed; RealMaxClient is unavailable")
            return None
