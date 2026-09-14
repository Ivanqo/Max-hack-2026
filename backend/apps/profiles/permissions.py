from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of a profile or admins to view/edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin':
            return True

        # Users can only access their own profile
        return obj.user == request.user


class IsStudentOrAdmin(permissions.BasePermission):
    """
    Permission to only allow students or admins to access student profiles.
    """

    def has_permission(self, request, view):
        return request.user.role in ['student', 'admin']


class TenantIsolationPermission(permissions.BasePermission):
    """
    Permission that enforces tenant isolation based on university.
    Students can only see profiles from their own university.
    Admins can see all profiles.
    """

    def has_permission(self, request, view):
        # Admin users bypass tenant isolation
        if request.user.role == 'admin':
            return True

        # Students must have a university set
        if request.user.role == 'student':
            return bool(request.user.university)

        return False

    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin':
            return True

        # Students can only access profiles from their own university
        if request.user.role == 'student':
            return obj.university == request.user.university

        return False


class CanCompleteOnboarding(permissions.BasePermission):
    """
    Permission to allow users to complete their own onboarding.
    """

    def has_object_permission(self, request, view, obj):
        # Admin users can complete any onboarding
        if request.user.role == 'admin':
            return True

        # Users can only complete their own onboarding
        return obj.user == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admins to edit, but allow read access to authenticated users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.role == 'admin'
