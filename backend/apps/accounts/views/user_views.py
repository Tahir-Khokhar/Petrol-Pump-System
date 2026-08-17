from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsOwnerOrAdmin, IsPumpManager, IsSuperAdmin
from apps.accounts.serializers.auth_serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for user management.

    - SUPER_ADMIN: full CRUD on all users
    - PUMP_MANAGER: list and retrieve employees
    - Users can update their own profile (partial_update)
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['created_at', 'updated_at', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """Return appropriate permission classes based on the action."""
        if self.action == 'create':
            return [IsAuthenticated(), IsSuperAdmin()]
        if self.action == 'list':
            return [IsAuthenticated(), (IsSuperAdmin() | IsPumpManager())]
        if self.action == 'retrieve':
            return [IsAuthenticated(), (IsSuperAdmin() | IsPumpManager())]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_paginated_response(self, data):
        """Override to wrap pagination in standard response format."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': 'Users retrieved successfully.',
            'data': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'results': data,
            },
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """List users with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        # PUMP_MANAGER can only see non-SUPER_ADMIN users
        if request.user.role == User.Role.PUMP_MANAGER:
            queryset = queryset.exclude(role=User.Role.SUPER_ADMIN)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Users retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single user by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'User retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new user. Only SUPER_ADMIN can perform this action."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'success': True,
            'message': 'User created successfully.',
            'data': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a user's information."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'success': True,
            'message': 'User updated successfully.',
            'data': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a user's information."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
