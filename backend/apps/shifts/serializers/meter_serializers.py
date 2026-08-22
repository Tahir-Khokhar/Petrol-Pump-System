from rest_framework import serializers

from apps.shifts.models import MeterReading


class MeterReadingSerializer(serializers.ModelSerializer):
    """Full serializer for meter readings."""
    shift_uuid = serializers.UUIDField(source='shift.uuid', read_only=True)
    pump_name = serializers.CharField(source='shift.pump.name', read_only=True)
    nozzle_number = serializers.CharField(source='nozzle.nozzle_number', read_only=True)
    recorded_by_email = serializers.EmailField(source='recorded_by.email', read_only=True, default=None)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MeterReading
        fields = [
            'uuid', 'shift', 'shift_uuid', 'pump_name', 'nozzle', 'nozzle_number',
            'opening_reading', 'closing_reading', 'fuel_dispensed',
            'sales_count', 'date', 'recorded_by', 'recorded_by_email', 'recorded_by_name',
            'notes', 'created_at',
        ]

    def get_recorded_by_name(self, obj):
        return f'{obj.recorded_by.first_name} {obj.recorded_by.last_name}'.strip()

    read_only_fields = ['uuid', 'fuel_dispensed', 'created_at']


class MeterReadingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating meter readings."""
    class Meta:
        model = MeterReading
        fields = ['shift', 'nozzle', 'opening_reading', 'closing_reading', 'date', 'notes']

    def validate(self, attrs):
        closing = attrs.get('closing_reading')
        opening = attrs.get('opening_reading')
        if closing is not None and opening is not None and closing < opening:
            raise serializers.ValidationError('Closing reading cannot be less than opening reading.')
        return attrs

    def create(self, validated_data):
        opening = validated_data['opening_reading']
        closing = validated_data.get('closing_reading')
        fuel_dispensed = None
        if closing is not None:
            fuel_dispensed = closing - opening

        instance = MeterReading.objects.create(
            **validated_data,
            fuel_dispensed=fuel_dispensed,
            recorded_by=self.context['request'].user,
        )
        return instance
