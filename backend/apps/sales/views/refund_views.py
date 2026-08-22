from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sales.filters import RefundFilter
from apps.sales.models import Refund, Sale
from apps.sales.permissions import CanProcessRefund
from apps.sales.serializers.refund_serializers import RefundCreateSerializer, RefundSerializer
from apps.sales.services import process_refund


@extend_schema_view(
    list=extend_schema(
        summary='List refunds',
        description='List refunds. Only SUPER_ADMIN/PUMP_MANAGER can create.',
        tags=['Refunds'],
    ),
    retrieve=extend_schema(
        summary='Retrieve refund',
        description='Retrieve a single refund by UUID.',
        tags=['Refunds'],
    ),
    create=extend_schema(
        summary='Create refund',
        description='Create a refund for a completed sale. SUPER_ADMIN/PUMP_MANAGER only.',
        tags=['Refunds'],
    ),
)
class RefundViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for refund management.

    - All authenticated users: list and retrieve
    - SUPER_ADMIN / PUMP_MANAGER: create refunds
    """
    queryset = Refund.objects.select_related('sale', 'processed_by').all()
    lookup_field = 'uuid'
    filterset_class = RefundFilter
    ordering_fields = ['refund_number', 'amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanProcessRefund()]
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
            'message': 'Refunds retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Refund retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        # Get the sale instance from validated UUID
        sale_uuid = serializer.validated_data['sale']
        sale = Sale.objects.get(uuid=sale_uuid)

        try:
            refund = process_refund({
                'sale': sale,
                'amount': serializer.validated_data['amount'],
                'reason': serializer.validated_data['reason'],
            }, request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': 'Refund created successfully.',
            'data': RefundSerializer(refund).data,
        }, status=status.HTTP_201_CREATED)
