"""
Mock MAX Client - Implementation for development and testing.
"""
import logging
import uuid
from typing import Dict, Any, Optional
from .client import MaxClient

logger = logging.getLogger(__name__)


class MockMaxClient(MaxClient):
    """
    Mock implementation of MAX API client for development and testing.
    Simulates MAX API responses without making actual network requests.
    """

    def __init__(self):
        """Initialize mock client."""
        self._notifications = {}
        self._available = True
        logger.info("MockMaxClient initialized")

    def send_notification(
        self,
        student_id: str,
        title: str,
        message: str,
        opportunity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulate sending a notification through MAX.

        Args:
            student_id: Unique identifier for the student
            title: Notification title
            message: Notification message content
            opportunity_id: Optional opportunity identifier
            metadata: Optional additional metadata

        Returns:
            Dict with simulated response
        """
        message_id = str(uuid.uuid4())

        self._notifications[message_id] = {
            'student_id': student_id,
            'title': title,
            'message': message,
            'opportunity_id': opportunity_id,
            'metadata': metadata or {},
            'status': 'delivered',
            'sent_at': None  # Would be timestamp in real implementation
        }

        logger.info(
            f"Mock notification sent - ID: {message_id}, Student: {student_id}, "
            f"Title: {title}"
        )

        return {
            'success': True,
            'message_id': message_id,
            'provider': 'mock',
            'error': None
        }

    def get_notification_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get simulated notification status.

        Args:
            message_id: The message identifier

        Returns:
            Dict containing status information
        """
        notification = self._notifications.get(message_id)

        if not notification:
            logger.warning(f"Notification {message_id} not found in mock storage")
            return {
                'success': False,
                'status': 'not_found',
                'error': 'Notification not found'
            }

        return {
            'success': True,
            'status': notification['status'],
            'message_id': message_id,
            'error': None
        }

    def is_available(self) -> bool:
        """
        Check if mock client is available (always True unless manually disabled).

        Returns:
            bool: Availability status
        """
        return self._available

    def set_available(self, available: bool):
        """
        Manually set availability for testing failure scenarios.

        Args:
            available: Whether the mock client should be available
        """
        self._available = available
        logger.info(f"MockMaxClient availability set to: {available}")

    def clear_notifications(self):
        """Clear all stored notifications (useful for testing)."""
        self._notifications.clear()
        logger.info("MockMaxClient notifications cleared")

    def get_all_notifications(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stored notifications (useful for testing).

        Returns:
            Dict of all notifications keyed by message_id
        """
        return self._notifications.copy()
