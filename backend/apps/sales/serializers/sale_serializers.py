from decimal import Decimal

from rest_framework import serializers

from apps.sales.models import Sale


class CustomerSummarySerializer(serializers.Serializer):
    """Minimal customer representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_corporate = serializers.BooleanField(read_only=True)


class EmployeeSummarySerializer(serializers.Serializer):
    """Minimal employee (user) representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)


class PumpSummarySerializer(serializers.Serializer):
    """Minimal pump representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    pump_number = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class NozzleSummarySerializer(serializers.Serializer):
    """Minimal nozzle representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    nozzle_number = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class FuelTypeSummarySerializer(serializers.Serializer):
    """Minimal fuel type representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    name = serializers.CharField(read_only=True)


class PaymentSummarySerializer(serializers.Serializer):
    """Minimal payment representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    payment_reference = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)


class RefundSummarySerializer(serializers.Serializer):
    """Minimal refund representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    refund_number = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)


class SaleListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing sales."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    customer = CustomerSummarySerializer(read_only=True)
    employee = EmployeeSummarySerializer(read_only=True)
    pump = PumpSummarySerializer(read_only=True)
    fuel_type = FuelTypeSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    # Flat fields for frontend convenience
    customer_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    pump_name = serializers.SerializerMethodField()
    fuel_type_name = serializers.SerializerMethodField()
    amount = serializers.DecimalField(source='total_amount', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'receipt_number', 'customer', 'employee',
            'pump', 'fuel_type', 'quantity', 'total_amount',
            'payment_method', 'payment_method_display',
            'status', 'status_display', 'created_at',
            'customer_name', 'employee_name', 'pump_name',
            'fuel_type_name', 'amount',
        ]

    def get_customer_name(self, obj):
        if obj.customer:
            return getattr(obj.customer, 'full_name', '') or getattr(obj.customer, 'name', '')
        return None

    def get_employee_name(self, obj):
        if obj.employee:
            return f'{obj.employee.first_name} {obj.employee.last_name}'.strip()
        return None

    def get_pump_name(self, obj):
        if obj.pump:
            return obj.pump.name or f'Pump #{obj.pump.pump_number}'
        return None

    def get_fuel_type_name(self, obj):
        if obj.fuel_type:
            return obj.fuel_type.name
        return None


class SaleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for sale detail/retrieve with all nested data."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    customer = CustomerSummarySerializer(read_only=True)
    employee = EmployeeSummarySerializer(read_only=True)
    pump = PumpSummarySerializer(read_only=True)
    nozzle = NozzleSummarySerializer(read_only=True)
    fuel_type = FuelTypeSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True, source='payments.all')
    refunds = RefundSummarySerializer(many=True, read_only=True, source='refunds.all')
    fuel_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'receipt_number', 'customer', 'employee',
            'pump', 'nozzle', 'fuel_type',
            'quantity', 'price_per_unit', 'subtotal',
            'discount', 'tax_rate', 'tax_amount', 'total_amount',
            'payment_method', 'payment_method_display',
            'status', 'status_display', 'notes',
            'payments', 'refunds', 'created_at',
            'fuel_type_name',
        ]

    def get_fuel_type_name(self, obj):
        return obj.fuel_type.name if obj.fuel_type else None


class SaleCreateSerializer(serializers.Serializer):
    """Serializer for creating a sale. Server calculates all totals."""

    customer = serializers.UUIDField(required=False, allow_null=True)
    pump = serializers.UUIDField()
    nozzle = serializers.UUIDField()
    fuel_type = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    payment_method = serializers.ChoiceField(choices=Sale.PaymentMethod.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_customer(self, value):
        if value is not None:
            from apps.customers.models import Customer
            try:
                Customer.objects.get(uuid=value)
            except Customer.DoesNotExist:
                raise serializers.ValidationError('Customer not found.')
        return value

    def validate_pump(self, value):
        from apps.pumps.models import Pump
        try:
            pump = Pump.objects.get(uuid=value)
        except Pump.DoesNotExist:
            raise serializers.ValidationError('Pump not found.')
        if pump.status != Pump.Status.ACTIVE:
            raise serializers.ValidationError('Pump is not active.')
        return value

    def validate_nozzle(self, value):
        from apps.pumps.models import Nozzle
        try:
            nozzle = Nozzle.objects.select_related('pump').get(uuid=value)
        except Nozzle.DoesNotExist:
            raise serializers.ValidationError('Nozzle not found.')
        if nozzle.status != Nozzle.Status.ACTIVE:
            raise serializers.ValidationError('Nozzle is not active.')
        # Store pump UUID on the nozzle for cross-validation
        self._nozzle_pump_uuid = nozzle.pump.uuid
        self._nozzle_fuel_type_uuid = nozzle.fuel_type.uuid
        return value

    def validate(self, attrs):
        # Cross-validate nozzle belongs to pump
        if 'pump' in attrs and hasattr(self, '_nozzle_pump_uuid'):
            if attrs['pump'] != self._nozzle_pump_uuid:
                raise serializers.ValidationError({
                    'nozzle': 'Nozzle does not belong to the specified pump.'
                })

        # Validate quantity
        quantity = attrs.get('quantity', Decimal('0'))
        if quantity <= Decimal('0'):
            raise serializers.ValidationError({'quantity': 'Quantity must be greater than zero.'})

        # Validate discount
        discount = attrs.get('discount', Decimal('0'))
        if discount < Decimal('0'):
            raise serializers.ValidationError({'discount': 'Discount cannot be negative.'})

        # Corporate credit limit check
        customer_uuid = attrs.get('customer')
        if customer_uuid is not None:
            from apps.customers.models import Customer
            customer = Customer.objects.get(uuid=customer_uuid)
            if customer.is_corporate:
                from apps.fuel.models import FuelType
                from apps.pumps.models import Nozzle
                nozzle = Nozzle.objects.select_related('fuel_type').get(uuid=attrs['nozzle'])
                fuel_type = nozzle.fuel_type
                price = fuel_type.current_price
                subtotal = quantity * price
                tax_amount = subtotal * Decimal('0')  # default tax_rate=0
                estimated_total = subtotal + tax_amount - discount
                potential_balance = customer.outstanding_balance + estimated_total
                if customer.credit_limit > 0 and potential_balance > customer.credit_limit:
                    raise serializers.ValidationError({
                        'customer': (
                            f'Credit limit exceeded. Outstanding: {customer.outstanding_balance}, '
                            f'Credit Limit: {customer.credit_limit}, '
                            f'Estimated Total: {estimated_total}'
                        )
                    })

        return attrs


class SaleReceiptSerializer(serializers.ModelSerializer):
    """Read-only serializer with full details for receipt display."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    customer = CustomerSummarySerializer(read_only=True)
    employee = EmployeeSummarySerializer(read_only=True)
    pump = PumpSummarySerializer(read_only=True)
    nozzle = NozzleSummarySerializer(read_only=True)
    fuel_type = FuelTypeSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    fuel_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'receipt_number', 'customer', 'employee',
            'pump', 'nozzle', 'fuel_type',
            'quantity', 'price_per_unit', 'subtotal',
            'discount', 'tax_rate', 'tax_amount', 'total_amount',
            'payment_method', 'payment_method_display',
            'status', 'status_display', 'notes', 'created_at',
            'fuel_type_name',
        ]

    def get_fuel_type_name(self, obj):
        return obj.fuel_type.name if obj.fuel_type else None
