from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.employees.filters import EmployeeFilter
from apps.employees.models import Employee
from apps.employees.permissions import CanManageEmployees, CanViewEmployees
from apps.employees.serializers.employee_serializers import (
    EmployeeCreateSerializer,
    EmployeeListSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)


class EmployeeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for employee management.

    - SUPER_ADMIN: full CRUD
    - PUMP_MANAGER: full CRUD
    - CASHIER / PUMP_ATTENDANT: list and retrieve only
    - ACCOUNTANT: list and retrieve only
    - CUSTOMER: no access
    """
    queryset = Employee.objects.select_related('user', 'assigned_pump').all()
    lookup_field = 'uuid'
    filterset_class = EmployeeFilter
    search_fields = ['name', 'employee_id', 'phone']
    ordering_fields = ['name', 'employee_id', 'job_role', 'status', 'hire_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        if self.action == 'create':
            return EmployeeCreateSerializer
        if self.action in ('update', 'partial_update'):
            return EmployeeUpdateSerializer
        return EmployeeSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageEmployees()]
        return [IsAuthenticated(), CanViewEmployees()]

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
        """List employees with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Employees retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single employee by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Employee retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new employee. Uses transaction.atomic for user role update."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        with transaction.atomic():
            user_uuid = validated_data.pop('user')
            pump_uuid = validated_data.pop('assigned_pump', None)

            # Fetch user
            try:
                user = User.objects.select_for_update().get(uuid=user_uuid)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found.',
                    'data': None,
                }, status=status.HTTP_400_BAD_REQUEST)

            # Fetch pump if provided
            assigned_pump = None
            if pump_uuid:
                from apps.pumps.models import Pump
                try:
                    assigned_pump = Pump.objects.get(uuid=pump_uuid)
                except Pump.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Pump not found.',
                        'data': None,
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Sync user role with job_role
            job_role = validated_data['job_role']
            mapped_role = Employee.ROLE_MAPPING.get(job_role)
            if mapped_role and user.role != mapped_role:
                user.role = mapped_role
                user.save(update_fields=['role'])

            # Create employee
            employee = Employee.objects.create(
                user=user,
                assigned_pump=assigned_pump,
                **validated_data,
            )

        return Response({
            'success': True,
            'message': 'Employee created successfully.',
            'data': EmployeeSerializer(employee, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update an employee."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        with transaction.atomic():
            # Handle assigned_pump update
            pump_was_provided = 'assigned_pump' in validated_data
            pump_uuid = validated_data.pop('assigned_pump', None)
            if pump_uuid is not None:
                from apps.pumps.models import Pump
                try:
                    instance.assigned_pump = Pump.objects.get(uuid=pump_uuid)
                except Pump.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Pump not found.',
                        'data': None,
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif pump_was_provided:
                # Allow clearing the pump if assigned_pump is explicitly null
                instance.assigned_pump = None

            # Handle job_role update — sync user role
            job_role = validated_data.get('job_role')
            if job_role:
                mapped_role = Employee.ROLE_MAPPING.get(job_role)
                if mapped_role:
                    user = User.objects.select_for_update().get(uuid=instance.user.uuid)
                    if user.role != mapped_role:
                        user.role = mapped_role
                        user.save(update_fields=['role'])

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return Response({
            'success': True,
            'message': 'Employee updated successfully.',
            'data': EmployeeSerializer(instance, context={'request': request}).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update an employee."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete an employee."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Employee deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)
