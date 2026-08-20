from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fuel.filters import TankFilter
from apps.fuel.models import Tank
from apps.fuel.permissions import IsFuelManager
from apps.fuel.serializers.tank_serializers import (
    TankSerializer,
    TankListSerializer,
    TankStockAdjustmentSerializer,
)


class TankViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for tank management.

    - SUPER_ADMIN / PUMP_MANAGER / INVENTORY_MANAGER: full CRUD
    - Other authenticated users: list and retrieve only
    """
    queryset = Tank.objects.select_related('fuel_type').all()
    lookup_field = 'uuid'
    filterset_class = TankFilter
    search_fields = ['tank_number', 'location']
    ordering_fields = ['tank_number', 'capacity', 'current_quantity', 'status', 'created_at']
    ordering = ['tank_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return TankListSerializer
        return TankSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsFuelManager()]
        return [IsAuthenticated()]

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
        """List tanks with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Tanks retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single tank by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Tank retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new tank."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tank = serializer.save()

        return Response({
            'success': True,
            'message': 'Tank created successfully.',
            'data': TankSerializer(tank).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a tank."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        tank = serializer.save()

        return Response({
            'success': True,
            'message': 'Tank updated successfully.',
            'data': TankSerializer(tank).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a tank."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a tank."""
        instance = self.get_object()
        tank_number = instance.tank_number
        instance.delete()

        return Response({
            'success': True,
            'message': f'Tank "{tank_number}" deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)


class TankStockAdjustmentView(APIView):
    """
    POST endpoint to adjust a tank's stock level.

    Only SUPER_ADMIN, PUMP_MANAGER, and INVENTORY_MANAGER can adjust stock.
    """
    permission_classes = [IsAuthenticated, IsFuelManager]

    def post(self, request, *args, **kwargs):
        serializer = TankStockAdjustmentSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        tank = serializer.save()

        return Response({
            'success': True,
            'message': f'Stock for tank "{tank.tank_number}" adjusted successfully. New quantity: {tank.current_quantity}.',
            'data': TankSerializer(tank).data,
        }, status=status.HTTP_200_OK)
