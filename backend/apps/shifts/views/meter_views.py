from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.shifts.filters import MeterReadingFilter
from apps.shifts.models import MeterReading
from apps.shifts.permissions import CanCreateMeterReading
from apps.shifts.serializers.meter_serializers import (
    MeterReadingCreateSerializer,
    MeterReadingSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary='List meter readings',
        description='List all meter readings.',
        tags=['Meter Readings'],
    ),
    retrieve=extend_schema(
        summary='Retrieve meter reading',
        description='Retrieve a single meter reading by UUID.',
        tags=['Meter Readings'],
    ),
    create=extend_schema(
        summary='Create meter reading',
        description='Create a new meter reading. SUPER_ADMIN/PUMP_MANAGER/CASHIER/PUMP_ATTENDANT can create.',
        tags=['Meter Readings'],
    ),
)
class MeterReadingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for meter readings."""
    queryset = MeterReading.objects.select_related(
        'shift', 'nozzle', 'shift__employee', 'shift__pump', 'recorded_by'
    ).all()
    lookup_field = 'uuid'
    filterset_class = MeterReadingFilter
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.action == 'create':
            return MeterReadingCreateSerializer
        return MeterReadingSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateMeterReading()]
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
            'message': 'Meter readings retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Meter reading retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': 'Meter reading created successfully.',
            'data': MeterReadingSerializer(instance).data,
        }, status=status.HTTP_201_CREATED)
