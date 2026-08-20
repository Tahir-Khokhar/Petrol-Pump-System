from rest_framework import serializers

from apps.pumps.models import Nozzle
from apps.pumps.services import update_nozzle_meter


class PumpSummarySerializer(serializers.Serializer):
    """Minimal pump representation for nested serialization."""
    uuid = serializers.UUIDField(read_only=True)
    pump_number = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class FuelTypeSummarySerializer(serializers.Serializer):
    """Minimal fuel type representation for nested serialization."""
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)


class NozzleSerializer(serializers.ModelSerializer):
    """Full serializer for nozzle create/update/retrieve."""

    pump = PumpSummarySerializer(read_only=True)
    fuel_type = FuelTypeSummarySerializer(read_only=True)
    pump_id = serializers.UUIDField(write_only=True)
    fuel_type_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Nozzle
        fields = [
            'uuid', 'nozzle_number', 'pump', 'pump_id',
            'fuel_type', 'fuel_type_id',
            'opening_meter_reading', 'closing_meter_reading',
            'current_meter_reading', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def validate_pump_id(self, value):
        from apps.pumps.models import Pump

        try:
            Pump.objects.get(uuid=value)
        except Pump.DoesNotExist:
            raise serializers.ValidationError(
                'Pump not found.',
                code='not_found',
            )
        return value

    def validate_fuel_type_id(self, value):
        from apps.fuel.models import FuelType

        try:
            FuelType.objects.get(uuid=value)
        except FuelType.DoesNotExist:
            raise serializers.ValidationError(
                'Fuel type not found.',
                code='not_found',
            )
        return value

    def create(self, validated_data):
        from apps.pumps.models import Pump
        from apps.fuel.models import FuelType

        pump = Pump.objects.get(uuid=validated_data.pop('pump_id'))
        fuel_type = FuelType.objects.get(uuid=validated_data.pop('fuel_type_id'))
        return Nozzle.objects.create(pump=pump, fuel_type=fuel_type, **validated_data)

    def update(self, instance, validated_data):
        if 'pump_id' in validated_data:
            from apps.pumps.models import Pump
            validated_data['pump'] = Pump.objects.get(uuid=validated_data.pop('pump_id'))
        if 'fuel_type_id' in validated_data:
            from apps.fuel.models import FuelType
            validated_data['fuel_type'] = FuelType.objects.get(uuid=validated_data.pop('fuel_type_id'))
        return super().update(instance, validated_data)


class NozzleListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    pump = PumpSummarySerializer(read_only=True)
    pump_name = serializers.CharField(source='pump.name', read_only=True)
    fuel_type = FuelTypeSummarySerializer(read_only=True)
    fuel_type_name = serializers.CharField(source='fuel_type.name', read_only=True)

    class Meta:
        model = Nozzle
        fields = [
            'uuid', 'nozzle_number', 'pump', 'pump_name', 'fuel_type', 'fuel_type_name',
            'opening_meter_reading', 'current_meter_reading', 'status',
        ]


class NozzleMeterUpdateSerializer(serializers.Serializer):
    """Serializer for updating a nozzle's meter reading."""

    nozzle = serializers.UUIDField(write_only=True)
    closing_meter_reading = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        write_only=True,
    )

    def validate_nozzle(self, value):
        try:
            return Nozzle.objects.get(uuid=value)
        except Nozzle.DoesNotExist:
            raise serializers.ValidationError(
                'Nozzle not found.',
                code='not_found',
            )

    def validate(self, attrs):
        nozzle = attrs.get('nozzle')
        closing_reading = attrs.get('closing_meter_reading')

        if nozzle is not None and closing_reading is not None:
            if closing_reading < nozzle.opening_meter_reading:
                raise serializers.ValidationError(
                    f'Closing meter reading ({closing_reading}) must be greater than or equal '
                    f'to opening meter reading ({nozzle.opening_meter_reading}).',
                    code='invalid_reading',
                )

            if closing_reading < nozzle.current_meter_reading:
                raise serializers.ValidationError(
                    f'Closing meter reading ({closing_reading}) cannot be less than '
                    f'current meter reading ({nozzle.current_meter_reading}).',
                    code='invalid_reading',
                )

        return attrs

    def create(self, validated_data):
        nozzle = validated_data['nozzle']
        closing_reading = validated_data['closing_meter_reading']
        user = self.context['request'].user

        nozzle = update_nozzle_meter(nozzle, closing_reading, user)
        return nozzle
