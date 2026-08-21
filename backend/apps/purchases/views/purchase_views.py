from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.purchases.filters import PurchaseFilter
from apps.purchases.models import Purchase
from apps.purchases.permissions import CanManagePurchases
from apps.purchases.serializers.purchase_serializers import (
    PurchaseCreateSerializer,
    PurchaseListSerializer,
    PurchaseSerializer,
)
from apps.purchases.services import create_purchase


@extend_schema_view(
    list=extend_schema(
        summary='List purchases',
        description='List all purchases. SUPER_ADMIN/PUMP_MANAGER/INVENTORY_MANAGER can create.',
        tags=['Purchases'],
    ),
    retrieve=extend_schema(
        summary='Retrieve purchase',
        description='Retrieve a single purchase by UUID.',
        tags=['Purchases'],
    ),
)
class PurchaseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for full CRUD on purchases."""
    queryset = Purchase.objects.select_related(
        'supplier', 'fuel_type', 'tank', 'inventory_item', 'created_by'
    ).all()
    lookup_field = 'uuid'
    filterset_class = PurchaseFilter
    search_fields = ['purchase_number', 'invoice_number']
    ordering_fields = ['purchase_number', 'total_cost', 'purchase_date', 'payment_status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseCreateSerializer
        if self.action == 'list':
            return PurchaseListSerializer
        return PurchaseSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManagePurchases()]
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
            'message': 'Purchases retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Purchase retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = PurchaseCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            purchase = serializer.save()
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(str(e))
        return Response({
            'success': True,
            'message': 'Purchase created successfully.',
            'data': PurchaseSerializer(purchase).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = PurchaseSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Purchase updated successfully.',
            'data': PurchaseSerializer(instance).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Purchase deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)
