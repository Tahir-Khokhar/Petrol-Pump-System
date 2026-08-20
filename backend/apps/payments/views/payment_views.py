import uuid

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.payments.filters import PaymentFilter
from apps.payments.models import Payment
from apps.payments.permissions import CanManagePayments
from apps.payments.serializers.payment_serializers import (
    PaymentCreateSerializer,
    PaymentListSerializer,
    PaymentSerializer,
)
from apps.sales.models import Sale


@extend_schema_view(
    list=extend_schema(
        summary='List payments',
        description='List payments. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT full access. CASHIER can list own.',
        tags=['Payments'],
    ),
    retrieve=extend_schema(
        summary='Retrieve payment',
        description='Retrieve a single payment by UUID.',
        tags=['Payments'],
    ),
    create=extend_schema(
        summary='Create payment',
        description='Manually record a payment. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT only.',
        tags=['Payments'],
    ),
)
class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for payment management.

    - SUPER_ADMIN / PUMP_MANAGER / ACCOUNTANT: full access
    - CASHIER: list/retrieve own payments
    """
    queryset = Payment.objects.select_related('sale', 'processed_by').all()
    lookup_field = 'uuid'
    filterset_class = PaymentFilter
    ordering_fields = ['payment_reference', 'amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        if self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanManagePayments()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role in [User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER, User.Role.ACCOUNTANT, User.Role.CASHIER]:
            return queryset

        return queryset.none()

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
            'message': 'Payments retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Payment retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create manual payment
        sale = Sale.objects.get(uuid=serializer.validated_data['sale'])
        payment_reference = f'PAY-MANUAL-{uuid.uuid4().hex[:8].upper()}'

        payment = Payment.objects.create(
            payment_reference=payment_reference,
            sale=sale,
            amount=serializer.validated_data['amount'],
            payment_method=serializer.validated_data['payment_method'],
            transaction_ref=serializer.validated_data.get('transaction_ref', ''),
            processed_by=request.user,
            notes=serializer.validated_data.get('notes', ''),
            status=Payment.Status.COMPLETED,
        )

        return Response({
            'success': True,
            'message': 'Payment created successfully.',
            'data': PaymentSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)
