from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.sales.filters import SaleFilter
from apps.sales.models import Sale
from apps.sales.permissions import CanCreateSale, CanViewAllSales, IsSaleOwnerOrAdmin
from apps.sales.serializers.sale_serializers import (
    SaleCreateSerializer,
    SaleDetailSerializer,
    SaleListSerializer,
    SaleReceiptSerializer,
)
from apps.sales.services import create_sale


@extend_schema_view(
    list=extend_schema(
        summary='List sales',
        description='List sales. SUPER_ADMIN/PUMP_MANAGER/ACCOUNTANT see all. CASHIER sees own. CUSTOMER sees own.',
        tags=['Sales'],
    ),
    retrieve=extend_schema(
        summary='Retrieve sale',
        description='Retrieve a single sale by UUID.',
        tags=['Sales'],
    ),
)
class SaleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for viewing sales.

    - SUPER_ADMIN / PUMP_MANAGER / ACCOUNTANT: list all, retrieve any
    - CASHIER: list own sales, retrieve own
    - CUSTOMER: list own sales (via customer profile), retrieve own
    """
    queryset = Sale.objects.select_related(
        'customer', 'employee', 'pump', 'nozzle', 'fuel_type'
    ).all()
    lookup_field = 'uuid'
    filterset_class = SaleFilter
    search_fields = ['receipt_number']
    ordering_fields = ['receipt_number', 'total_amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SaleListSerializer
        return SaleDetailSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsSaleOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role in [User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER, User.Role.ACCOUNTANT, User.Role.CASHIER]:
            return queryset

        if user.role == User.Role.CUSTOMER:
            try:
                from apps.customers.models import Customer
                customer = Customer.objects.get(user=user)
                return queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return queryset.none()

        return queryset.none()

    def get_paginated_response(self, data):
        """Override to include success/message wrapper with pagination metadata."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': 'Sales retrieved successfully.',
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
            'message': 'Sales retrieved successfully.',
            'data': {
                'results': serializer.data,
                'count': len(serializer.data),
            },
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Sale retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary='Create a sale',
    description='Create a new fuel sale. All totals are calculated server-side. CASHIER/PUMP_MANAGER/SUPER_ADMIN only.',
    request=SaleCreateSerializer,
    tags=['Sales'],
)
class CreateSaleView(APIView):
    """
    POST endpoint to create a sale.

    Uses the full transaction-based sale creation service.
    Only CASHIER, PUMP_MANAGER, and SUPER_ADMIN can create sales.
    """
    permission_classes = [IsAuthenticated, CanCreateSale]

    def post(self, request, *args, **kwargs):
        serializer = SaleCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            sale = create_sale(serializer.validated_data, request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': 'Sale created successfully.',
            'data': SaleDetailSerializer(sale).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Get sale receipt',
    description='Retrieve the receipt details for a sale.',
    tags=['Sales'],
)
class SaleReceiptView(APIView):
    """
    GET endpoint to retrieve a sale receipt.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        try:
            sale = Sale.objects.select_related(
                'customer', 'employee', 'pump', 'nozzle', 'fuel_type'
            ).get(uuid=uuid)
        except Sale.DoesNotExist:
            raise NotFound('Sale not found.')

        return Response({
            'success': True,
            'message': 'Receipt retrieved successfully.',
            'data': SaleReceiptSerializer(sale).data,
        }, status=status.HTTP_200_OK)
