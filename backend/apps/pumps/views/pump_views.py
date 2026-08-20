from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pumps.filters import PumpFilter
from apps.pumps.models import Pump
from apps.pumps.permissions import IsPumpManagerOrAbove
from apps.pumps.serializers.pump_serializers import (
    PumpAssignEmployeeSerializer,
    PumpListSerializer,
    PumpSerializer,
    PumpStatusUpdateSerializer,
)
from apps.pumps.services import assign_employee_to_pump, update_pump_status


class PumpViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for pump management.

    - SUPER_ADMIN / PUMP_MANAGER: full create, update, partial_update, destroy
    - All authenticated users: list and retrieve
    """
    queryset = Pump.objects.select_related(
        'assigned_employee',
    ).prefetch_related(
        'fuel_types', 'nozzles',
    ).all()
    lookup_field = 'uuid'
    filterset_class = PumpFilter
    search_fields = ['name', 'pump_number']
    ordering_fields = ['pump_number', 'name', 'status', 'created_at', 'updated_at']
    ordering = ['pump_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return PumpListSerializer
        return PumpSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsPumpManagerOrAbove()]
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
        """List pumps with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Pumps retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single pump by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Pump retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new pump. Only SUPER_ADMIN or PUMP_MANAGER."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pump = serializer.save()

        return Response({
            'success': True,
            'message': 'Pump created successfully.',
            'data': PumpSerializer(pump).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a pump."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        pump = serializer.save()

        return Response({
            'success': True,
            'message': 'Pump updated successfully.',
            'data': PumpSerializer(pump).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a pump."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a pump. Only SUPER_ADMIN or PUMP_MANAGER."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Pump deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)


class PumpAssignEmployeeView(APIView):
    """
    POST endpoint to assign an employee to a pump.

    Only SUPER_ADMIN and PUMP_MANAGER can assign employees.
    """
    permission_classes = [IsAuthenticated, IsPumpManagerOrAbove]

    def post(self, request, *args, **kwargs):
        serializer = PumpAssignEmployeeSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        pump = serializer.validated_data['pump']
        employee = serializer.validated_data['employee']

        try:
            pump = assign_employee_to_pump(pump, employee, request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': f'Employee {employee.email} assigned to pump {pump.pump_number} successfully.',
            'data': PumpSerializer(pump).data,
        }, status=status.HTTP_200_OK)


class PumpStatusUpdateView(APIView):
    """
    PATCH/POST endpoint to update a pump's status.

    Only SUPER_ADMIN and PUMP_MANAGER can update status.
    """
    permission_classes = [IsAuthenticated, IsPumpManagerOrAbove]

    def post(self, request, *args, **kwargs):
        """Update pump status via POST."""
        pump_uuid = request.data.get('pump')
        if not pump_uuid:
            raise ValidationError('Pump UUID is required.')
        return self._update_status(request, pump_uuid)

    def patch(self, request, *args, **kwargs):
        """Update pump status via PATCH."""
        pump_uuid = request.data.get('pump')
        if not pump_uuid:
            raise ValidationError('Pump UUID is required.')
        return self._update_status(request, pump_uuid)

    def _update_status(self, request, pump_uuid):
        try:
            pump = Pump.objects.get(uuid=pump_uuid)
        except Pump.DoesNotExist:
            raise ValidationError('Pump not found.')

        serializer = PumpStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        try:
            pump = update_pump_status(pump, new_status, request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': f'Pump {pump.pump_number} status updated to {new_status} successfully.',
            'data': PumpSerializer(pump).data,
        }, status=status.HTTP_200_OK)
