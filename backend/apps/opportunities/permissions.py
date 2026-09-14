from rest_framework import permissions


CONTENT_MANAGERS = ['editor', 'institute_admin', 'university_admin', 'mentor', 'organizer', 'admin']
TENANT_ADMINS = ['institute_admin', 'university_admin', 'organizer', 'admin']


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user


class IsSameUniversityOrAdmin(permissions.BasePermission):
    """
    Tenant isolation: Users can only access opportunities from their university.
    Admins have access to all universities.
    """

    def has_permission(self, request, view):
        # Admins have full access
        if request.user.role in ['admin', 'university_admin']:
            return True

        # All authenticated users can view
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role in ['admin', 'university_admin']:
            return True

        # Users can only access opportunities from their university
        if hasattr(obj, 'university'):
            return obj.university == request.user.university

        # For SavedOpportunity objects, check through the relationship
        if hasattr(obj, 'opportunity'):
            return obj.opportunity.university == request.user.university

        return False


class CanManageOpportunity(permissions.BasePermission):
    """
    Permission for creating and managing opportunities.
    Students can view, mentors and organizers can create/edit, admins can do everything.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admins have full access
        if request.user.role in ['admin', 'university_admin']:
            return True

        # For read-only requests, all authenticated users have access
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, only mentors, organizers, and admins
        return request.user.role in CONTENT_MANAGERS

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admins have full access
        if request.user.role in ['admin', 'university_admin']:
            return True

        # Read permissions for all authenticated users from same university
        if request.method in permissions.SAFE_METHODS:
            return obj.university == request.user.university

        # Write permissions for owner (mentor/organizer who created it)
        if obj.created_by == request.user:
            return True

        # Organizers can edit any opportunity in their university
        if request.user.role in TENANT_ADMINS and obj.university == request.user.university:
            return True

        return False


class CanVerifyOpportunity(permissions.BasePermission):
    """
    Only organizers and admins can verify opportunities.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in TENANT_ADMINS

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admins can verify any opportunity
        if request.user.role in ['admin', 'university_admin']:
            return True

        # Organizers can verify opportunities in their university
        if request.user.role in ['organizer', 'institute_admin']:
            return obj.university == request.user.university

        return False


class IsStudent(permissions.BasePermission):
    """
    Permission for student-only actions like saving opportunities.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'
