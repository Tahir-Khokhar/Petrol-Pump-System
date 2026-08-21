from rest_framework import serializers

from apps.purchases.models import Purchase
from apps.purchases.services import create_purchase, update_purchase_payment_status


class PurchaseSerializer(serializers.ModelSerializer):
    """Full serializer for purchases."""
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    fuel_type_name = serializers.CharField(source='fuel_type.name', read_only=True, default=None)
    tank_number = serializers.CharField(source='tank.tank_number', read_only=True, default=None)

    class Meta:
        model = Purchase
        fields = [
            'uuid', 'purchase_number', 'supplier', 'supplier_name',
            'fuel_type', 'fuel_type_name', 'tank', 'tank_number',
            'inventory_item', 'quantity', 'price_per_unit', 'total_cost',
            'purchase_date', 'invoice_number', 'payment_status',
            'notes', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'purchase_number', 'total_cost', 'created_at', 'updated_at']


class PurchaseListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for purchases."""
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    fuel_type_name = serializers.CharField(source='fuel_type.name', read_only=True, default=None)
    tank_number = serializers.CharField(source='tank.tank_number', read_only=True, default=None)
    unit_price = serializers.DecimalField(source='price_per_unit', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'uuid', 'purchase_number', 'supplier', 'supplier_name',
            'fuel_type', 'fuel_type_name', 'tank', 'tank_number',
            'quantity', 'unit_price', 'total_cost', 'purchase_date',
            'payment_status', 'created_at',
        ]


class PurchaseCreateSerializer(serializers.Serializer):
    """Serializer for creating purchases."""
    supplier = serializers.UUIDField()
    fuel_type = serializers.UUIDField(required=False, allow_null=True)
    tank = serializers.UUIDField(required=False, allow_null=True)
    inventory_item = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = serializers.DateField()
    invoice_number = serializers.CharField(required=False, default='', allow_blank='')
    notes = serializers.CharField(required=False, default='', allow_blank='')
    payment_status = serializers.ChoiceField(
        choices=Purchase.PaymentStatus.choices,
        default=Purchase.PaymentStatus.PENDING,
    )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def validate_price_per_unit(self, value):
        if value < 0:
            raise serializers.ValidationError('Price per unit cannot be negative.')
        return value

    def create(self, validated_data):
        return create_purchase(validated_data, self.context['request'].user)
