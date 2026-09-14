from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a subscription to edit it.
    Implements tenant isolation - users can only access their own subscriptions.
    """

    def has_object_permission(self, request, view, obj):
        """
        Read permissions are allowed to the owner only.
        Write permissions are only allowed to the owner of the subscription.
        """
        # Check if the subscription belongs to the authenticated user
        return obj.student == request.user


class IsSubscriptionOwner(permissions.BasePermission):
    """
    Permission class that enforces tenant isolation.
    Users can only access subscriptions they own.
    """

    def has_permission(self, request, view):
        """
        All authenticated users can create subscriptions.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Users can only access their own subscriptions.
        """
        return obj.student == request.user


class IsStudentRole(permissions.BasePermission):
    """
    Permission to check if user has student role.
    Only students should create subscriptions.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and has student role.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
        )


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission for admin users or subscription owners.
    Admins can see all subscriptions, users can only see their own.
    """

    def has_permission(self, request, view):
        """
        Allow access to authenticated users.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Admins can access any subscription.
        Regular users can only access their own subscriptions.
        """
        if request.user.role == 'admin' or request.user.is_staff:
            return True
        return obj.student == request.user
