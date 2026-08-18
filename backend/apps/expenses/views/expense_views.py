from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.expenses.filters import ExpenseFilter
from apps.expenses.models import Expense
from apps.expenses.permissions import CanManageExpenses
from apps.expenses.serializers.expense_serializers import (
    ExpenseCreateSerializer,
    ExpenseListSerializer,
    ExpenseSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary='List expenses',
        description='List all expenses. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT can create. Others read.',
        tags=['Expenses'],
    ),
    retrieve=extend_schema(
        summary='Retrieve expense',
        description='Retrieve a single expense by UUID.',
        tags=['Expenses'],
    ),
    create=extend_schema(
        summary='Create expense',
        description='Create a new expense. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT only.',
        tags=['Expenses'],
    ),
    update=extend_schema(
        summary='Update expense',
        description='Update an expense. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT only.',
        tags=['Expenses'],
    ),
    partial_update=extend_schema(
        summary='Partially update expense',
        description='Partially update an expense. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT only.',
        tags=['Expenses'],
    ),
    destroy=extend_schema(
        summary='Delete expense',
        description='Delete an expense. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT only.',
        tags=['Expenses'],
    ),
)
class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for full CRUD on expenses."""
    queryset = Expense.objects.select_related('employee', 'created_by').all()
    lookup_field = 'uuid'
    filterset_class = ExpenseFilter
    search_fields = ['description', 'receipt_reference']
    ordering_fields = ['expense_date', 'amount', 'category', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExpenseListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ExpenseCreateSerializer
        return ExpenseSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageExpenses()]
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
            'message': 'Expenses retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Expense retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Expense created successfully.',
            'data': ExpenseSerializer(instance).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Expense updated successfully.',
            'data': ExpenseSerializer(instance).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Expense deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)
