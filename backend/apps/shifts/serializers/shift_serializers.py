from rest_framework import serializers

from apps.shifts.models import Shift


class ShiftSerializer(serializers.ModelSerializer):
    """Full serializer for shifts."""
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    pump_number = serializers.CharField(source='pump.pump_number', read_only=True)

    class Meta:
        model = Shift
        fields = [
            'uuid', 'employee', 'employee_email', 'pump', 'pump_number',
            'start_time', 'end_time', 'opening_cash', 'closing_cash',
            'expected_cash', 'actual_cash', 'cash_difference',
            'total_sales', 'total_transactions', 'status', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class ShiftListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for shifts."""
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.SerializerMethodField()
    pump_number = serializers.CharField(source='pump.pump_number', read_only=True)
    pump_name = serializers.CharField(source='pump.name', read_only=True)

    class Meta:
        model = Shift
        fields = [
            'uuid', 'employee', 'employee_email', 'employee_name', 'pump', 'pump_number', 'pump_name',
            'start_time', 'end_time', 'opening_cash', 'expected_cash', 'actual_cash', 'cash_difference',
            'total_sales', 'total_transactions', 'status', 'created_at',
        ]

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'.strip()


class OpenShiftSerializer(serializers.Serializer):
    """Serializer for opening a shift."""
    employee = serializers.UUIDField()
    pump = serializers.UUIDField()
    opening_cash = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)

    def validate_opening_cash(self, value):
        if value < 0:
            raise serializers.ValidationError('Opening cash cannot be negative.')
        return value

    def validate(self, attrs):
        from apps.shifts.models import Shift
        from apps.pumps.models import Pump

        pump = Pump.objects.get(uuid=attrs['pump'])
        existing_open = Shift.objects.filter(
            pump=pump,
            status=Shift.Status.OPEN,
        ).exists()
        if existing_open:
            raise serializers.ValidationError(
                'There is already an open shift for this pump. Close it before opening a new one.'
            )
        return attrs


class CloseShiftSerializer(serializers.Serializer):
    """Serializer for closing a shift."""
    actual_cash = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_actual_cash(self, value):
        if value < 0:
            raise serializers.ValidationError('Actual cash cannot be negative.')
        return value
