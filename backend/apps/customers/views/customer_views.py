from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.customers.filters import CustomerFilter
from apps.customers.models import Customer
from apps.customers.permissions import CanManageCustomers
from apps.customers.serializers.customer_serializers import (
    CorporateCustomerSerializer,
    CustomerCreateSerializer,
    CustomerListSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
)


class CustomerViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for customer management.

    - SUPER_ADMIN / PUMP_MANAGER: full CRUD
    - CASHIER / PUMP_ATTENDANT: list and retrieve only
    - CUSTOMER: can only see own profile
    """
    queryset = Customer.objects.select_related('user').prefetch_related('vehicles').all()
    lookup_field = 'uuid'
    filterset_class = CustomerFilter
    search_fields = ['full_name', 'phone', 'company_name']
    ordering_fields = ['full_name', 'phone', 'status', 'is_corporate', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        if self.action == 'create':
            # Check if corporate customer creation
            if self.request.data.get('is_corporate'):
                return CorporateCustomerSerializer
            return CustomerCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CustomerUpdateSerializer
        return CustomerSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageCustomers()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # CUSTOMER role can only see own profile
        if user.role == User.Role.CUSTOMER:
            try:
                customer_uuid = user.customer_profile.uuid
                return queryset.filter(uuid=customer_uuid)
            except Customer.DoesNotExist:
                return queryset.none()

        return queryset

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
        """List customers with pagination and filtering."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Customers retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single customer by UUID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Customer retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new customer. Only SUPER_ADMIN or PUMP_MANAGER."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()

        return Response({
            'success': True,
            'message': 'Customer created successfully.',
            'data': CustomerSerializer(customer).data,
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a customer."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()

        return Response({
            'success': True,
            'message': 'Customer updated successfully.',
            'data': CustomerSerializer(customer).data,
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a customer."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a customer. Only SUPER_ADMIN or PUMP_MANAGER."""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Customer deleted successfully.',
            'data': None,
        }, status=status.HTTP_200_OK)


class CustomerMyProfileView(APIView):
    """
    GET endpoint for customer role to see their own profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Customer profile not found.',
                'data': None,
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(customer)
        return Response({
            'success': True,
            'message': 'Customer profile retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
