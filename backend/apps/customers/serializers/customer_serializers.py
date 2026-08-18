from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.customers.models.vehicle import Vehicle


class VehicleDetailSerializer(serializers.ModelSerializer):
    """Full vehicle representation for detail view."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    customer = serializers.UUIDField(source='customer.uuid', read_only=True)
    preferred_fuel_type = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'customer', 'registration_number', 'vehicle_type',
            'make', 'model_name', 'year', 'color',
            'preferred_fuel_type', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_preferred_fuel_type(self, obj):
        if obj.preferred_fuel_type:
            return {
                'id': str(obj.preferred_fuel_type.uuid),
                'name': obj.preferred_fuel_type.name,
                'code': obj.preferred_fuel_type.code,
            }
        return None


class VehicleSummarySerializer(serializers.Serializer):
    """Minimal vehicle representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    registration_number = serializers.CharField(read_only=True)
    vehicle_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class CustomerSerializer(serializers.ModelSerializer):
    """Full serializer for customer create/update/retrieve."""

    vehicles_count = serializers.SerializerMethodField(read_only=True)
    vehicles = VehicleDetailSerializer(many=True, read_only=True)
    user = serializers.UUIDField(source='user.uuid', read_only=True, default=None)

    class Meta:
        model = Customer
        fields = [
            'uuid', 'user', 'full_name', 'phone', 'email', 'address',
            'is_corporate', 'company_name', 'tax_number',
            'credit_limit', 'outstanding_balance', 'status',
            'vehicles_count', 'vehicles',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'outstanding_balance', 'created_at', 'updated_at']

    def get_vehicles_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'vehicles' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['vehicles'])
        return obj.vehicles.count()


class CustomerListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    vehicles_count = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(source='full_name', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'uuid', 'full_name', 'name', 'phone', 'email',
            'is_corporate', 'company_name',
            'credit_limit', 'outstanding_balance', 'status', 'is_active',
            'vehicles_count',
        ]

    def get_is_active(self, obj):
        return obj.status == 'ACTIVE'

    def get_vehicles_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'vehicles' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['vehicles'])
        return obj.vehicles.count()


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a customer."""

    class Meta:
        model = Customer
        fields = [
            'full_name', 'phone', 'email', 'address',
            'is_corporate', 'company_name', 'tax_number',
            'credit_limit', 'status',
        ]

    def validate_credit_limit(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError(
                'Credit limit must be zero or positive.',
                code='invalid_credit_limit',
            )
        return value

    def validate_phone(self, value):
        if value:
            qs = Customer.objects.filter(phone=value)
            if self.instance:
                qs = qs.exclude(uuid=self.instance.uuid)
            if qs.exists():
                raise serializers.ValidationError(
                    'A customer with this phone number already exists.',
                    code='unique',
                )
        return value


class CustomerUpdateSerializer(CustomerCreateSerializer):
    """Serializer for updating a customer."""

    class Meta(CustomerCreateSerializer.Meta):
        extra_kwargs = {
            field: {'required': False}
            for field in CustomerCreateSerializer.Meta.fields
        }

    def validate_credit_limit(self, value):
        if value is not None and value < Decimal('0'):
            raise serializers.ValidationError(
                'Credit limit must be zero or positive.',
                code='invalid_credit_limit',
            )
        return value


class CorporateCustomerSerializer(CustomerCreateSerializer):
    """Serializer for creating a corporate customer.

    Extends CustomerCreate with company_name required, tax_number, credit_limit required > 0.
    """

    class Meta(CustomerCreateSerializer.Meta):
        extra_kwargs = {
            'company_name': {'required': True, 'allow_blank': False},
            'tax_number': {'required': False, 'allow_blank': True},
            'credit_limit': {'required': True},
            'is_corporate': {'default': True},
        }

    def validate_credit_limit(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError(
                'Corporate customer credit limit must be greater than zero.',
                code='invalid_credit_limit',
            )
        return value
