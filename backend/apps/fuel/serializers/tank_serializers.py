from rest_framework import serializers

from apps.fuel.models import Tank
from apps.fuel.services import adjust_tank_stock


class TankSerializer(serializers.ModelSerializer):
    """Full serializer for tank create/update/retrieve."""

    fuel_type_name = serializers.CharField(
        source='fuel_type.name', read_only=True,
    )
    fuel_type_code = serializers.CharField(
        source='fuel_type.code', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Tank
        fields = [
            'uuid', 'tank_number', 'fuel_type', 'fuel_type_name', 'fuel_type_code',
            'capacity', 'current_quantity', 'minimum_quantity',
            'location', 'status', 'status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class TankListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    fuel_type_name = serializers.CharField(
        source='fuel_type.name', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Tank
        fields = [
            'uuid', 'tank_number', 'fuel_type', 'fuel_type_name',
            'capacity', 'current_quantity', 'minimum_quantity',
            'status', 'status_display',
        ]


class TankStockAdjustmentSerializer(serializers.Serializer):
    """Serializer for adjusting tank stock levels.

    On create, updates current_quantity with transaction.atomic and select_for_update.
    """

    tank = serializers.UUIDField(write_only=True)
    adjustment_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        write_only=True,
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        write_only=True,
    )

    def validate_tank(self, value):
        try:
            tank = Tank.objects.select_related('fuel_type').get(uuid=value)
        except Tank.DoesNotExist:
            raise serializers.ValidationError(
                'Tank not found.',
                code='not_found',
            )
        return tank

    def validate_adjustment_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError(
                'Adjustment quantity cannot be zero.',
                code='invalid_adjustment',
            )
        return value

    def create(self, validated_data):
        tank = validated_data['tank']
        adjustment_quantity = validated_data['adjustment_quantity']
        reason = validated_data.get('reason', '')
        user = self.context['request'].user

        try:
            tank = adjust_tank_stock(
                tank=tank,
                adjustment_quantity=adjustment_quantity,
                user=user,
                reason=reason,
            )
        except ValueError as e:
            raise serializers.ValidationError(str(e), code='invalid_adjustment')

        return tank
