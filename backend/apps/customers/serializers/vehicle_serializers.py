from rest_framework import serializers

from apps.customers.models.vehicle import Vehicle


class FuelTypeSummarySerializer(serializers.Serializer):
    """Minimal fuel type representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)


class CustomerSummarySerializer(serializers.Serializer):
    """Minimal customer representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)


class VehicleSerializer(serializers.ModelSerializer):
    """Full serializer for vehicle create/update/retrieve."""

    customer = CustomerSummarySerializer(read_only=True)
    customer_id = serializers.UUIDField(write_only=True)
    preferred_fuel_type = FuelTypeSummarySerializer(read_only=True)
    preferred_fuel_type_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vehicle
        fields = [
            'uuid', 'customer', 'customer_id',
            'registration_number', 'vehicle_type',
            'make', 'model_name', 'year', 'color',
            'preferred_fuel_type', 'preferred_fuel_type_id',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def validate_customer_id(self, value):
        from apps.customers.models import Customer
        try:
            Customer.objects.get(uuid=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError(
                'Customer not found.',
                code='not_found',
            )
        return value

    def validate_preferred_fuel_type_id(self, value):
        if value is not None:
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
        customer_id = validated_data.pop('customer_id')
        fuel_type_id = validated_data.pop('preferred_fuel_type_id', None)

        from apps.customers.models import Customer
        validated_data['customer'] = Customer.objects.get(uuid=customer_id)

        if fuel_type_id:
            from apps.fuel.models import FuelType
            validated_data['preferred_fuel_type'] = FuelType.objects.get(uuid=fuel_type_id)

        return Vehicle.objects.create(**validated_data)

    def update(self, instance, validated_data):
        customer_id = validated_data.pop('customer_id', None)
        fuel_type_id = validated_data.pop('preferred_fuel_type_id', None)

        if customer_id is not None:
            from apps.customers.models import Customer
            instance.customer = Customer.objects.get(uuid=customer_id)

        if fuel_type_id is not None:
            if fuel_type_id:
                from apps.fuel.models import FuelType
                instance.preferred_fuel_type = FuelType.objects.get(uuid=fuel_type_id)
            else:
                instance.preferred_fuel_type = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class VehicleListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    customer = CustomerSummarySerializer(read_only=True)
    preferred_fuel_type = FuelTypeSummarySerializer(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'uuid', 'customer', 'registration_number', 'vehicle_type',
            'make', 'model_name', 'year', 'color', 'preferred_fuel_type', 'status',
        ]


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a vehicle with validations."""

    customer_id = serializers.UUIDField(write_only=True)
    preferred_fuel_type_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vehicle
        fields = [
            'customer_id', 'registration_number', 'vehicle_type',
            'make', 'model_name', 'year', 'color',
            'preferred_fuel_type_id', 'status',
        ]

    def validate_customer_id(self, value):
        from apps.customers.models import Customer
        try:
            Customer.objects.get(uuid=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError(
                'Customer not found.',
                code='not_found',
            )
        return value

    def validate_registration_number(self, value):
        qs = Vehicle.objects.filter(registration_number=value)
        if self.instance:
            qs = qs.exclude(uuid=self.instance.uuid)
        if qs.exists():
            raise serializers.ValidationError(
                'A vehicle with this registration number already exists.',
                code='unique',
            )
        return value

    def validate_preferred_fuel_type_id(self, value):
        if value is not None:
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
        customer_id = validated_data.pop('customer_id')
        fuel_type_id = validated_data.pop('preferred_fuel_type_id', None)

        from apps.customers.models import Customer
        validated_data['customer'] = Customer.objects.get(uuid=customer_id)

        if fuel_type_id:
            from apps.fuel.models import FuelType
            validated_data['preferred_fuel_type'] = FuelType.objects.get(uuid=fuel_type_id)

        return Vehicle.objects.create(**validated_data)
