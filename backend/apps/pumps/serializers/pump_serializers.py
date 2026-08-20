from rest_framework import serializers

from apps.pumps.models import Pump


class FuelTypeSummarySerializer(serializers.Serializer):
    """Minimal fuel type representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    name = serializers.CharField(read_only=True)


class AssignedEmployeeSummarySerializer(serializers.Serializer):
    """Minimal user representation for assigned employee."""
    uuid = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)


class PumpSerializer(serializers.ModelSerializer):
    """Full serializer for pump create/update/retrieve."""

    fuel_types = FuelTypeSummarySerializer(many=True, read_only=True)
    fuel_type_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )
    assigned_employee = AssignedEmployeeSummarySerializer(read_only=True)
    assigned_employee_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Pump
        fields = [
            'uuid', 'pump_number', 'name', 'location', 'status',
            'assigned_employee', 'assigned_employee_id',
            'installation_date', 'last_maintenance_date',
            'fuel_types', 'fuel_type_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def validate_fuel_type_ids(self, value):
        from apps.fuel.models import FuelType

        valid_ids = []
        for ft_id in value:
            try:
                FuelType.objects.get(uuid=ft_id)
                valid_ids.append(ft_id)
            except FuelType.DoesNotExist:
                raise serializers.ValidationError(
                    f'Fuel type with id {ft_id} does not exist.',
                    code='not_found',
                )
        return valid_ids

    def validate_assigned_employee_id(self, value):
        if value is not None:
            from apps.accounts.models import User

            try:
                User.objects.get(uuid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f'User with id {value} does not exist.',
                    code='not_found',
                )
        return value

    def create(self, validated_data):
        fuel_type_ids = validated_data.pop('fuel_type_ids', [])
        assigned_employee_id = validated_data.pop('assigned_employee_id', None)

        if assigned_employee_id:
            from apps.accounts.models import User
            validated_data['assigned_employee'] = User.objects.get(uuid=assigned_employee_id)

        pump = Pump.objects.create(**validated_data)

        if fuel_type_ids:
            from apps.fuel.models import FuelType
            fuel_types = FuelType.objects.filter(uuid__in=fuel_type_ids)
            pump.fuel_types.set(fuel_types)

        return pump

    def update(self, instance, validated_data):
        fuel_type_ids = validated_data.pop('fuel_type_ids', None)
        assigned_employee_id = validated_data.pop('assigned_employee_id', None)

        if assigned_employee_id is not None:
            from apps.accounts.models import User
            try:
                instance.assigned_employee = User.objects.get(uuid=assigned_employee_id)
            except User.DoesNotExist:
                instance.assigned_employee = None
        elif 'assigned_employee_id' in self.initial_data and assigned_employee_id is None:
            instance.assigned_employee = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if fuel_type_ids is not None:
            from apps.fuel.models import FuelType
            fuel_types = FuelType.objects.filter(uuid__in=fuel_type_ids)
            instance.fuel_types.set(fuel_types)

        return instance


class PumpListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    fuel_types = FuelTypeSummarySerializer(many=True, read_only=True)
    assigned_employee = AssignedEmployeeSummarySerializer(read_only=True)
    active_nozzles = serializers.SerializerMethodField()

    class Meta:
        model = Pump
        fields = [
            'uuid', 'pump_number', 'name', 'status', 'location',
            'fuel_types', 'assigned_employee', 'active_nozzles',
        ]

    def get_active_nozzles(self, obj):
        return obj.nozzles.filter(status='ACTIVE').count()


class PumpAssignEmployeeSerializer(serializers.Serializer):
    """Serializer for assigning an employee to a pump."""

    pump = serializers.UUIDField(write_only=True)
    employee = serializers.UUIDField(write_only=True)

    def validate_pump(self, value):
        try:
            return Pump.objects.get(uuid=value)
        except Pump.DoesNotExist:
            raise serializers.ValidationError(
                'Pump not found.',
                code='not_found',
            )

    def validate_employee(self, value):
        from apps.accounts.models import User

        try:
            return User.objects.get(uuid=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Employee not found.',
                code='not_found',
            )


class PumpStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating pump status."""

    status = serializers.ChoiceField(choices=Pump.Status.choices)
