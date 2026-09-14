from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or admin
        return obj == request.user or request.user.role == 'admin'


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsOrganizerOrAdmin(permissions.BasePermission):
    """
    Allows access only to organizer or admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['organizer', 'admin']
        )


class IsMentorOrganizerOrAdmin(permissions.BasePermission):
    """
    Allows access only to mentor, organizer or admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['mentor', 'organizer', 'admin']
        )


class TenantIsolationPermission(permissions.BasePermission):
    """
    Ensures tenant isolation based on university.
    Users can only access data from their own university unless they are admins.
    """

    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.role == 'admin':
            return True

        # If object has university attribute, check isolation
        if hasattr(obj, 'university'):
            return obj.university == request.user.university

        # If object is a user, check if it's the same user or same university
        if hasattr(obj, 'email'):
            return obj == request.user or obj.university == request.user.university

        return True


class IsAuthenticatedOrRegister(permissions.BasePermission):
    """
    Allow unauthenticated users to register, but require authentication for other actions.
    """

    def has_permission(self, request, view):
        # Allow POST for registration
        if request.method == 'POST':
            return True
        # Require authentication for other methods
        return request.user and request.user.is_authenticated
