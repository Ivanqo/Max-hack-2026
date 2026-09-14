"""
MAX Client Interface - Abstract base class for MAX API integration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MaxClient(ABC):
    """
    Abstract base class for MAX API clients.
    Defines the interface that all MAX client implementations must follow.
    """

    @abstractmethod
    def send_notification(
        self,
        student_id: str,
        title: str,
        message: str,
        opportunity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification through the MAX platform.

        Args:
            student_id: Unique identifier for the student
            title: Notification title
            message: Notification message content
            opportunity_id: Optional opportunity identifier
            metadata: Optional additional metadata

        Returns:
            Dict containing response from MAX API with keys:
                - success: bool indicating if notification was sent
                - message_id: Optional string identifier from MAX
                - error: Optional error message if failed

        Raises:
            Exception: If the notification fails to send
        """
        pass

    @abstractmethod
    def get_notification_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the delivery status of a notification.

        Args:
            message_id: The MAX message identifier

        Returns:
            Dict containing status information

        Raises:
            Exception: If status check fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the MAX API is currently available.

        Returns:
            bool: True if API is available, False otherwise
        """
        pass
