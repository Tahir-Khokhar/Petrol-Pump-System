from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.shifts.filters import ShiftFilter
from apps.shifts.models import Shift
from apps.shifts.permissions import CanManageShifts, CanOpenCloseShift
from apps.shifts.serializers.shift_serializers import (
    CloseShiftSerializer,
    OpenShiftSerializer,
    ShiftListSerializer,
    ShiftSerializer,
)
from apps.shifts.services import close_shift, open_shift


@extend_schema_view(
    list=extend_schema(
        summary='List shifts',
        description='List shifts. CASHIER sees own shifts. SUPER_ADMIN/PUMP_MANAGER sees all.',
        tags=['Shifts'],
    ),
    retrieve=extend_schema(
        summary='Retrieve shift',
        description='Retrieve a single shift by UUID.',
        tags=['Shifts'],
    ),
)
class ShiftViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for viewing shifts. No direct create/update - use open/close endpoints."""
    queryset = Shift.objects.select_related('employee', 'pump').all()
    lookup_field = 'uuid'
    filterset_class = ShiftFilter
    ordering_fields = ['start_time', 'status']
    ordering = ['-start_time']

    def get_serializer_class(self):
        if self.action == 'list':
            return ShiftListSerializer
        return ShiftSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role in [User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER, User.Role.CASHIER]:
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
            'message': 'Shifts retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Shift retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary='Open a shift',
    description='Open a new shift for an employee at a pump. CASHIER/PUMP_MANAGER/SUPER_ADMIN only.',
    request=OpenShiftSerializer,
    tags=['Shifts'],
)
class OpenShiftView(APIView):
    """POST endpoint to open a shift."""
    permission_classes = [IsAuthenticated, CanOpenCloseShift]

    def post(self, request, *args, **kwargs):
        serializer = OpenShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import User as UserModel
        from apps.pumps.models import Pump

        employee = UserModel.objects.get(uuid=serializer.validated_data['employee'])
        pump = Pump.objects.get(uuid=serializer.validated_data['pump'])
        opening_cash = serializer.validated_data.get('opening_cash', 0)

        try:
            shift = open_shift(employee, pump, opening_cash, request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': 'Shift opened successfully.',
            'data': ShiftSerializer(shift).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Close a shift',
    description='Close an open shift with cash reconciliation. CASHIER/PUMP_MANAGER/SUPER_ADMIN only.',
    tags=['Shifts'],
)
class CloseShiftView(APIView):
    """POST endpoint to close a shift. Expects shift UUID in URL."""
    permission_classes = [IsAuthenticated, CanOpenCloseShift]

    def post(self, request, uuid, *args, **kwargs):
        try:
            shift = Shift.objects.select_related('employee', 'pump').get(uuid=uuid)
        except Shift.DoesNotExist:
            raise NotFound('Shift not found.')

        serializer = CloseShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            shift = close_shift(shift, serializer.validated_data['actual_cash'], request.user)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            'success': True,
            'message': 'Shift closed successfully.',
            'data': ShiftSerializer(shift).data,
        }, status=status.HTTP_200_OK)
