from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.suppliers.filters import SupplierFilter
from apps.suppliers.models import Supplier
from apps.suppliers.permissions import CanManageSuppliers
from apps.suppliers.serializers.supplier_serializers import (
    SupplierCreateSerializer,
    SupplierListSerializer,
    SupplierSerializer,
    SupplierUpdateSerializer,
)


class SupplierViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for supplier management.

    - SUPER_ADMIN / PUMP_MANAGER / INVENTORY_MANAGER: full CRUD
    - Others: read-only (list and retrieve)
    """
    queryset = Supplier.objects.all()
    lookup_field = 'uuid'
    filterset_class = SupplierFilter
    search_fields = ['company_name', 'contact_person', 'phone']
    ordering_fields = ['company_name', 'contact_person', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        if self.action == 'create':
            return SupplierCreateSerializer
        if self.action in ('update', 'partial_update'):
            return SupplierUpdateSerializer
        return SupplierSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageSuppliers()]
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
        """List suppliers with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Suppliers retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single supplier by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Supplier retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new supplier."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()

        return Response({
            'success': True,
            'message': 'Supplier created successfully.',
            'data': SupplierSerializer(supplier).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a supplier."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()

        return Response({
            'success': True,
            'message': 'Supplier updated successfully.',
            'data': SupplierSerializer(supplier).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a supplier."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a supplier."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Supplier deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)
