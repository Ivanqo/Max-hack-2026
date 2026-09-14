from rest_framework import permissions


class IsStudentOwner(permissions.BasePermission):
    """
    Permission class to ensure students can only access their own notifications.
    Provides tenant isolation based on the student user.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and has a student role."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and organizers can access all notifications
        if request.user.role in ['admin', 'organizer', 'institute_admin', 'university_admin']:
            return True

        # Students can only access their own notifications
        return request.user.role == 'student'

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific notification."""
        # Admins and organizers have full access
        if request.user.role in ['admin', 'organizer', 'institute_admin', 'university_admin']:
            return True

        return obj.student == request.user


class IsOrganizerOrAdmin(permissions.BasePermission):
    """
    Permission class for organizers and admins only.
    Used for creating and managing notifications.
    """

    def has_permission(self, request, view):
        """Check if user is an organizer or admin."""
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['admin', 'organizer', 'institute_admin', 'university_admin', 'editor']


class TenantIsolationPermission(permissions.BasePermission):
    """
    Ensures notifications are filtered by university (tenant isolation).
    Only notifications for the user's university should be accessible.
    """

    def has_permission(self, request, view):
        """Always allow at the view level - filtering happens in queryset."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check university-level access for the notification."""
        # Admins have access to all universities
        if request.user.role in ['admin', 'university_admin']:
            return True

        if request.user.role == 'student':
            notification_university = obj.student.university if obj.student else None
            return request.user.university == notification_university

        # For organizers, verify university match
        if request.user.role == 'organizer' and hasattr(request.user, 'university'):
            notification_university = obj.student.university if obj.student else None
            return request.user.university == notification_university

        return False
