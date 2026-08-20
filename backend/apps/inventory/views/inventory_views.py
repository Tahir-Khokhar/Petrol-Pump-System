from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.filters import InventoryItemFilter, InventoryTransactionFilter
from apps.inventory.models import InventoryItem, InventoryTransaction
from apps.inventory.permissions import CanManageInventory
from apps.inventory.serializers.inventory_serializers import (
    InventoryItemCreateSerializer,
    InventoryItemListSerializer,
    InventoryItemSerializer,
    InventoryTransactionSerializer,
    StockAdjustmentSerializer,
)
from apps.inventory.services import adjust_stock, check_low_stock


@extend_schema_view(
    list=extend_schema(
        summary='List inventory items',
        description='List all inventory items. Filtered by category, is_active, is_low_stock.',
        tags=['Inventory'],
    ),
    retrieve=extend_schema(
        summary='Retrieve inventory item',
        description='Retrieve a single inventory item by UUID.',
        tags=['Inventory'],
    ),
    create=extend_schema(
        summary='Create inventory item',
        description='Create a new inventory item. SUPER_ADMIN/PUMP_MANAGER/INVENTORY_MANAGER only.',
        tags=['Inventory'],
    ),
    update=extend_schema(
        summary='Update inventory item',
        description='Update an inventory item. SUPER_ADMIN/PUMP_MANAGER/INVENTORY_MANAGER only.',
        tags=['Inventory'],
    ),
    partial_update=extend_schema(
        summary='Partially update inventory item',
        description='Partially update an inventory item. SUPER_ADMIN/PUMP_MANAGER/INVENTORY_MANAGER only.',
        tags=['Inventory'],
    ),
    destroy=extend_schema(
        summary='Delete inventory item',
        description='Delete an inventory item. SUPER_ADMIN/PUMP_MANAGER/INVENTORY_MANAGER only.',
        tags=['Inventory'],
    ),
)
class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet for full CRUD on inventory items."""
    queryset = InventoryItem.objects.all()
    lookup_field = 'uuid'
    filterset_class = InventoryItemFilter
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'sku', 'category', 'current_stock', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return InventoryItemListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return InventoryItemCreateSerializer
        return InventoryItemSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageInventory()]
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
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Inventory items retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Inventory item retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Inventory item created successfully.',
            'data': InventoryItemSerializer(instance).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Inventory item updated successfully.',
            'data': InventoryItemSerializer(instance).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Inventory item deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary='List inventory transactions',
        description='List inventory transactions. INVENTORY_MANAGER/PUMP_MANAGER/SUPER_ADMIN can create via stock-adjust.',
        tags=['Inventory'],
    ),
    retrieve=extend_schema(
        summary='Retrieve inventory transaction',
        description='Retrieve a single inventory transaction by UUID.',
        tags=['Inventory'],
    ),
)
class InventoryTransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only ViewSet for inventory transactions."""
    queryset = InventoryTransaction.objects.select_related(
        'inventory_item', 'performed_by'
    ).all()
    lookup_field = 'uuid'
    filterset_class = InventoryTransactionFilter
    ordering_fields = ['created_at', 'transaction_type']
    ordering = ['-created_at']
    serializer_class = InventoryTransactionSerializer

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
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Inventory transactions retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Inventory transaction retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary='Stock adjustment',
    description='Adjust stock for an inventory item. Uses transaction.atomic + select_for_update.',
    request=StockAdjustmentSerializer,
    tags=['Inventory'],
)
class StockAdjustmentView(APIView):
    """POST endpoint for stock adjustments."""
    permission_classes = [IsAuthenticated, CanManageInventory]

    def post(self, request, *args, **kwargs):
        serializer = StockAdjustmentSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            transaction = serializer.save()
        except ValueError as e:
            raise ValidationError(str(e))
        return Response({
            'success': True,
            'message': 'Stock adjusted successfully.',
            'data': InventoryTransactionSerializer(transaction).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Low stock items',
    description='Returns items where current_stock <= minimum_stock_level.',
    tags=['Inventory'],
)
class LowStockListView(APIView):
    """GET endpoint to list items below minimum stock level."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        items = check_low_stock()
        serializer = InventoryItemListSerializer(items, many=True)
        return Response({
            'success': True,
            'message': 'Low stock items retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
