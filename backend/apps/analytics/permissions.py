from rest_framework import permissions


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class ensuring only admins/organizers can access analytics
    and they can only see data for their own university (tenant isolation).
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and is an admin/organizer."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is admin or organizer
        if not (request.user.is_staff or request.user.is_superuser or
                getattr(request.user, 'role', None) in ['admin', 'organizer', 'institute_admin', 'university_admin']):
            return False

        return True


class IsTenantMember(permissions.BasePermission):
    """
    Permission class for tenant isolation - users can only access data
    from their own university.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and belongs to a university."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Ensure user has a university attribute
        if not hasattr(request.user, 'university') or not request.user.university:
            return False

        return True


class CanViewAnalytics(permissions.BasePermission):
    """
    Combined permission: user must be authenticated, be an admin/organizer,
    and have a university assigned for tenant isolation.
    """

    def has_permission(self, request, view):
        """Check if user can view analytics."""
        if not request.user or not request.user.is_authenticated:
            return False

        # User must belong to a university
        if not hasattr(request.user, 'university') or not request.user.university:
            return False

        # User must be admin or organizer
        user_role = getattr(request.user, 'role', None)
        is_admin = request.user.is_staff or request.user.is_superuser or user_role in [
            'admin', 'organizer', 'institute_admin', 'university_admin'
        ]

        return is_admin


def get_user_university(user):
    """
    Helper function to safely get the university from a user object.
    Returns None if user doesn't have a university.
    """
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'university', None)
