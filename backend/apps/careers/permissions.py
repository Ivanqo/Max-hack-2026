from rest_framework import permissions


CAREER_MANAGERS = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']


class IsSameUniversity(permissions.BasePermission):
    """
    Permission to ensure tenant isolation - users can only access
    data from their own university.
    """

    def has_permission(self, request, view):
        """Check if user has basic permission."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access specific object based on university."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can access everything
        if request.user.is_superuser:
            return True

        # Check university field on the object
        obj_university = getattr(obj, 'university', None)
        user_university = getattr(request.user, 'university', None)

        if obj_university and user_university:
            return obj_university == user_university

        return False


class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Permission for students to manage their own skills,
    others can only read.
    """

    def has_permission(self, request, view):
        """Check basic permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow read-only for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write operations only for students
        return request.user.role in ['student', 'admin']

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read-only for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admins can modify anything
        if request.user.role == 'admin' or request.user.is_superuser:
            return True

        # Students can only modify their own skills
        if hasattr(obj, 'student'):
            return obj.student.user == request.user

        return False


class IsOrganizerOrAdmin(permissions.BasePermission):
    """
    Permission for organizers and admins to manage career roles and skills.
    Students and mentors have read-only access.
    """

    def has_permission(self, request, view):
        """Check basic permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow read-only for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write operations for organizers and admins
        return request.user.role in CAREER_MANAGERS or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read-only for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write for organizers and admins
        if request.user.role in CAREER_MANAGERS or request.user.is_superuser:
            # Ensure they're from the same university
            obj_university = getattr(obj, 'university', None)
            user_university = getattr(request.user, 'university', None)

            if request.user.is_superuser:
                return True

            if obj_university and user_university:
                return obj_university == user_university

        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission for users to access their own data or admins to access all.
    """

    def has_permission(self, request, view):
        """Check basic permission."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and superusers can access everything
        if request.user.role in ['admin', 'university_admin'] or request.user.is_superuser:
            return True

        # Check if user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user

        return False
