from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fuel.filters import FuelTypeFilter
from apps.fuel.models import FuelType, FuelPriceHistory
from apps.fuel.permissions import IsSuperAdminOrPumpManager
from apps.fuel.serializers.fuel_type_serializers import (
    FuelTypeSerializer,
    FuelTypeListSerializer,
    FuelPriceHistorySerializer,
    FuelPriceUpdateSerializer,
)


class FuelTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for fuel type management.

    - SUPER_ADMIN / PUMP_MANAGER: full create, update, partial_update
    - All authenticated users: list and retrieve
    """
    queryset = FuelType.objects.all()
    lookup_field = 'uuid'
    filterset_class = FuelTypeFilter
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'current_price', 'created_at', 'updated_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return FuelTypeListSerializer
        return FuelTypeSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsAuthenticated(), IsSuperAdminOrPumpManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return super().get_queryset()

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
        """List fuel types with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Fuel types retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single fuel type by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Fuel type retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new fuel type. Only SUPER_ADMIN or PUMP_MANAGER."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fuel_type = serializer.save()

        return Response({
            'success': True,
            'message': 'Fuel type created successfully.',
            'data': FuelTypeSerializer(fuel_type).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a fuel type."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        fuel_type = serializer.save()

        return Response({
            'success': True,
            'message': 'Fuel type updated successfully.',
            'data': FuelTypeSerializer(fuel_type).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a fuel type."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class FuelPriceHistoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only ViewSet for fuel price history."""

    queryset = FuelPriceHistory.objects.select_related('fuel_type', 'changed_by').all()
    serializer_class = FuelPriceHistorySerializer
    lookup_field = 'uuid'
    filterset_fields = ['fuel_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

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
        """List fuel price history with pagination."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Fuel price history retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single price history entry."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Fuel price history entry retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class FuelPriceUpdateView(APIView):
    """
    POST endpoint to update a fuel type's price.

    Only SUPER_ADMIN and PUMP_MANAGER can change prices.
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOrPumpManager]

    def post(self, request, *args, **kwargs):
        serializer = FuelPriceUpdateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        fuel_type = serializer.save()

        return Response({
            'success': True,
            'message': f'Price for {fuel_type.name} updated to {fuel_type.current_price} successfully.',
            'data': FuelTypeSerializer(fuel_type).data,
        }, status=status.HTTP_200_OK)
