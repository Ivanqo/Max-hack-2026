from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Subscription
from .serializers import (
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer,
)
from .permissions import IsSubscriptionOwner


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student subscriptions with full CRUD operations.

    Implements tenant isolation - users can only access their own subscriptions.

    list: Get all subscriptions for the authenticated user
    create: Create a new subscription
    retrieve: Get a specific subscription (if owned by user)
    update: Update a subscription (if owned by user)
    partial_update: Partially update a subscription (if owned by user)
    destroy: Delete a subscription (if owned by user)

    Additional actions:
    - active: Get only active subscriptions
    - inactive: Get only inactive subscriptions
    - toggle_active: Toggle the active status of a subscription
    """
    permission_classes = [IsAuthenticated, IsSubscriptionOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'topic']
    search_fields = ['topic', 'filters']
    ordering_fields = ['created_at', 'updated_at', 'topic']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return subscriptions for the authenticated user only (tenant isolation).
        Admins can see all subscriptions if needed.
        """
        user = self.request.user

        # Admins can optionally see all subscriptions
        if user.role == 'admin' or user.is_staff:
            # Admin can filter by student_id query param
            student_id = self.request.query_params.get('student_id', None)
            if student_id:
                return Subscription.objects.filter(student_id=student_id)
            # By default, even admins see only their own
            return Subscription.objects.filter(student=user)

        # Regular users only see their own subscriptions (tenant isolation)
        return Subscription.objects.filter(student=user)

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new subscription for the authenticated user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            subscription = serializer.save()
            response_serializer = SubscriptionSerializer(subscription)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception:
            return Response(
                {'error': 'Failed to create subscription.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """
        Update a subscription (full update).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            subscription = serializer.save()
            response_serializer = SubscriptionSerializer(subscription)
            return Response(response_serializer.data)
        except Exception:
            return Response(
                {'error': 'Failed to update subscription.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a subscription.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a subscription.
        """
        try:
            instance = self.get_object()
            instance.delete()
            return Response(
                {'message': 'Subscription deleted successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception:
            return Response(
                {'error': 'Failed to delete subscription.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get only active subscriptions for the authenticated user.
        """
        queryset = self.get_queryset().filter(active=True)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inactive(self, request):
        """
        Get only inactive subscriptions for the authenticated user.
        """
        queryset = self.get_queryset().filter(active=False)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a subscription.
        """
        try:
            subscription = self.get_object()
            subscription.active = not subscription.active
            subscription.save()

            serializer = self.get_serializer(subscription)
            return Response(
                {
                    'message': f'Subscription {"activated" if subscription.active else "deactivated"} successfully.',
                    'subscription': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Failed to toggle subscription status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get subscription statistics for the authenticated user.
        """
        queryset = self.get_queryset()
        total = queryset.count()
        active = queryset.filter(active=True).count()
        inactive = queryset.filter(active=False).count()

        return Response({
            'total': total,
            'active': active,
            'inactive': inactive,
        })
