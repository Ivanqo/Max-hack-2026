from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationCreateSerializer
)
from .permissions import IsStudentOwner, IsOrganizerOrAdmin, TenantIsolationPermission


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.

    Students can list and retrieve their own notifications.
    Organizers and admins can create and manage all notifications.
    Implements tenant isolation based on university.
    """

    queryset = Notification.objects.select_related(
        'student',
        'opportunity'
    ).all()

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'opportunity']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Return appropriate permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOrganizerOrAdmin]
        else:
            permission_classes = [IsAuthenticated, IsStudentOwner, TenantIsolationPermission]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def get_queryset(self):
        """
        Filter queryset based on user role and university (tenant isolation).
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Platform superusers see all notifications.
        if user.is_superuser:
            return queryset

        # Tenant-scoped admins see notifications for their university.
        if user.role == 'admin':
            return queryset.filter(student__university=user.university)

        # Students see only their own notifications
        if user.role == 'student':
            return queryset.filter(student=user)

        # Organizers see notifications for their university
        if user.role == 'organizer' and hasattr(user, 'university'):
            return queryset.filter(student__university=user.university)

        # Default: no notifications
        return queryset.none()

    def list(self, request, *args, **kwargs):
        """
        List notifications for the current user.

        Query params:
        - status: Filter by status (pending, sent, failed)
        - opportunity: Filter by opportunity ID
        - search: Search in title and message
        - ordering: Order by field (created_at, sent_at)
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {'error': 'Failed to retrieve notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific notification.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Failed to retrieve notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Create a new notification.
        Only organizers and admins can create notifications.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Validate tenant isolation for organizers
            if request.user.role == 'organizer' and hasattr(request.user, 'university'):
                student = serializer.validated_data.get('student')
                if student and student.university != request.user.university:
                    return Response(
                        {'error': 'Cannot create notifications for students outside your university'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # Return full notification data
            instance = serializer.instance
            response_serializer = NotificationSerializer(instance)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        except Exception:
            return Response(
                {'error': 'Failed to create notification'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """
        Update a notification.
        Only organizers and admins can update notifications.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            # Validate tenant isolation for organizers
            if request.user.role == 'organizer' and hasattr(request.user, 'university'):
                if instance.student.university != request.user.university:
                    return Response(
                        {'error': 'Cannot update notifications outside your university'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # Return full notification data
            response_serializer = NotificationSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Failed to update notification'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a notification.
        Only organizers and admins can delete notifications.
        """
        try:
            instance = self.get_object()

            # Validate tenant isolation for organizers
            if request.user.role == 'organizer' and hasattr(request.user, 'university'):
                if instance.student.university != request.user.university:
                    return Response(
                        {'error': 'Cannot delete notifications outside your university'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Failed to delete notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unread(self, request):
        """
        Get count of unread (pending) notifications for the current student.
        """
        try:
            if request.user.role == 'student':
                count = Notification.objects.filter(
                    student=request.user,
                    read_at__isnull=True
                ).count()

                return Response({'count': count}, status=status.HTTP_200_OK)

            return Response(
                {'error': 'Only students can check unread notifications'},
                status=status.HTTP_403_FORBIDDEN
            )

        except Exception:
            return Response(
                {'error': 'Failed to count unread notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStudentOwner])
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read (sent).
        """
        try:
            notification = self.get_object()
            notification.mark_as_read()

            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Failed to mark notification as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
