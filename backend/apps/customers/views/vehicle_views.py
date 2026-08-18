from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.customers.filters import VehicleFilter
from apps.customers.models.vehicle import Vehicle
from apps.customers.permissions import CanManageCustomers
from apps.customers.serializers.vehicle_serializers import (
    VehicleCreateSerializer,
    VehicleListSerializer,
    VehicleSerializer,
)


class VehicleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for vehicle management.

    - SUPER_ADMIN / PUMP_MANAGER: full CRUD
    - CASHIER / PUMP_ATTENDANT: list and retrieve only
    - CUSTOMER: can only see own vehicles
    """
    queryset = Vehicle.objects.select_related('customer', 'preferred_fuel_type').all()
    lookup_field = 'uuid'
    filterset_class = VehicleFilter
    search_fields = ['registration_number']
    ordering_fields = ['registration_number', 'vehicle_type', 'status', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        if self.action == 'create':
            return VehicleCreateSerializer
        return VehicleSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageCustomers()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # CUSTOMER role can only see own vehicles
        if user.role == User.Role.CUSTOMER:
            try:
                customer_uuid = user.customer_profile.uuid
                return queryset.filter(customer__uuid=customer_uuid)
            except Exception:
                return queryset.none()

        return queryset

    def get_paginated_response(self, data):
        """Override to include success/message wrapper with pagination metadata."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': '',
            'data': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'results': data,
            },
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """List vehicles with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Vehicles retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single vehicle by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Vehicle retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new vehicle. Only SUPER_ADMIN or PUMP_MANAGER."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()

        return Response({
            'success': True,
            'message': 'Vehicle created successfully.',
            'data': VehicleSerializer(vehicle).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a vehicle."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = VehicleSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()

        return Response({
            'success': True,
            'message': 'Vehicle updated successfully.',
            'data': VehicleSerializer(vehicle).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a vehicle."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a vehicle. Only SUPER_ADMIN or PUMP_MANAGER."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Vehicle deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)
