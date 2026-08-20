from rest_framework import serializers

from apps.fuel.models import FuelType, FuelPriceHistory
from apps.fuel.services import update_fuel_price


class FuelTypeSerializer(serializers.ModelSerializer):
    """Full serializer for fuel type create/update/retrieve."""

    class Meta:
        model = FuelType
        fields = [
            'uuid', 'name', 'code', 'description', 'unit',
            'current_price', 'minimum_stock_level', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class FuelTypeListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (excludes description)."""

    class Meta:
        model = FuelType
        fields = [
            'uuid', 'name', 'code', 'unit',
            'current_price', 'minimum_stock_level', 'is_active',
        ]


class FuelPriceUpdateSerializer(serializers.Serializer):
    """Serializer for updating fuel prices.

    On create, creates a FuelPriceHistory entry and updates
    the FuelType's current_price.
    """

    fuel_type = serializers.UUIDField(write_only=True)
    new_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        write_only=True,
    )

    def validate_new_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'New price must be greater than zero.',
                code='invalid_price',
            )
        return value

    def validate_fuel_type(self, value):
        try:
            fuel_type = FuelType.objects.get(uuid=value)
        except FuelType.DoesNotExist:
            raise serializers.ValidationError(
                'Fuel type not found.',
                code='not_found',
            )
        return fuel_type

    def create(self, validated_data):
        fuel_type = validated_data['fuel_type']
        new_price = validated_data['new_price']
        reason = validated_data.get('reason', '')
        user = self.context['request'].user

        fuel_type = update_fuel_price(
            fuel_type=fuel_type,
            new_price=new_price,
            changed_by_user=user,
            reason=reason,
        )
        return fuel_type


class FuelPriceHistorySerializer(serializers.ModelSerializer):
    """Read-only serializer for fuel price history."""

    fuel_type_name = serializers.CharField(
        source='fuel_type.name', read_only=True,
    )
    fuel_type_code = serializers.CharField(
        source='fuel_type.code', read_only=True,
    )
    changed_by_email = serializers.EmailField(
        source='changed_by.email', read_only=True, default=None,
    )
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FuelPriceHistory
        fields = [
            'uuid', 'fuel_type', 'fuel_type_name', 'fuel_type_code',
            'previous_price', 'new_price', 'changed_by',
            'changed_by_email', 'changed_by_name', 'reason', 'created_at',
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return f'{obj.changed_by.first_name} {obj.changed_by.last_name}'.strip()
        return None
