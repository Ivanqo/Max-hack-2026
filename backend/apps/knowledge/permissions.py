from rest_framework import permissions


KNOWLEDGE_MANAGERS = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']


class IsSameUniversity(permissions.BasePermission):
    """
    Permission to ensure users can only access data from their own university.
    Implements tenant isolation based on university field.
    """

    message = "You can only access data from your own university."

    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can access any university
        if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', None) in KNOWLEDGE_MANAGERS:
            return True

        # For list/create views, user must have university set
        return hasattr(request.user, 'university') and request.user.university

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can access any university
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Ensure user can only access objects from their university
        user_university = getattr(request.user, 'university', None)
        obj_university = getattr(obj, 'university', None)

        return user_university and obj_university and user_university == obj_university


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to all authenticated users,
    but write access only to admins.
    """

    message = "Only administrators can modify this resource."

    def has_permission(self, request, view):
        """Check if user has permission for the action."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for staff/superuser
        return request.user.is_staff or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for staff/superuser
        return request.user.is_staff or request.user.is_superuser


class CanManageKnowledge(permissions.BasePermission):
    """
    Permission for managing knowledge items.
    - Staff/superuser can create, update, delete
    - Regular users can only read published items from their university
    """

    message = "You do not have permission to manage knowledge items."

    def has_permission(self, request, view):
        """Check if user has permission for the action."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Regular users can only read
        if request.method in permissions.SAFE_METHODS:
            return True

        # Regular users cannot create/update/delete
        return getattr(request.user, 'role', None) in KNOWLEDGE_MANAGERS

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', None) in KNOWLEDGE_MANAGERS:
            return True

        # Regular users can only read published items from their university
        if request.method in permissions.SAFE_METHODS:
            user_university = getattr(request.user, 'university', None)
            return (
                obj.published and
                user_university and
                obj.university == user_university
            )

        # Regular users cannot modify
        return False


class CanReportKnowledge(permissions.BasePermission):
    """
    Permission for reporting knowledge items.
    - Authenticated users can create reports for their own university
    - Only admins can view all reports and resolve them
    """

    message = "You do not have permission to access this report."

    def has_permission(self, request, view):
        """Check if user has permission for the action."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', None) in KNOWLEDGE_MANAGERS:
            return True

        # Regular users can create reports and view their own
        if request.method in ['POST', 'GET']:
            return hasattr(request.user, 'university') and request.user.university

        # Other methods (PUT, PATCH, DELETE) only for admins
        return False

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can access all reports
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Users can only access their own reports
        return obj.student == request.user


class IsAdminUser(permissions.BasePermission):
    """
    Permission to allow access only to admin users (staff or superuser).
    """

    message = "Only administrators can access this resource."

    def has_permission(self, request, view):
        """Check if user is admin."""
        return (
            request.user and
            request.user.is_authenticated and
            (
                request.user.is_staff or
                request.user.is_superuser or
                getattr(request.user, 'role', None) in KNOWLEDGE_MANAGERS
            )
        )
