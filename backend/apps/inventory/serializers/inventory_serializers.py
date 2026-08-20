from rest_framework import serializers

from apps.inventory.models import InventoryItem, InventoryTransaction
from apps.inventory.services import adjust_stock


class InventoryItemSerializer(serializers.ModelSerializer):
    """Full serializer for inventory items."""
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            'uuid', 'name', 'sku', 'category', 'description', 'unit',
            'current_stock', 'minimum_stock_level', 'cost_price',
            'selling_price', 'is_active', 'is_low_stock', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_is_low_stock(self, obj):
        return obj.current_stock <= obj.minimum_stock_level


class InventoryItemListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for inventory items."""
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            'uuid', 'name', 'sku', 'category', 'current_stock',
            'minimum_stock_level', 'cost_price', 'unit', 'selling_price', 'is_active', 'is_low_stock',
        ]

    def get_is_low_stock(self, obj):
        return obj.current_stock <= obj.minimum_stock_level


class InventoryItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating inventory items."""

    class Meta:
        model = InventoryItem
        fields = [
            'name', 'sku', 'category', 'description', 'unit',
            'current_stock', 'minimum_stock_level', 'cost_price',
            'selling_price', 'is_active',
        ]

    def validate_sku(self, value):
        qs = InventoryItem.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(uuid=self.instance.uuid)
        if qs.exists():
            raise serializers.ValidationError('An inventory item with this SKU already exists.')
        return value

    def validate_cost_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Cost price must be greater than zero.')
        return value

    def validate_selling_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Selling price must be greater than zero.')
        return value

    def validate_minimum_stock_level(self, value):
        if value < 0:
            raise serializers.ValidationError('Minimum stock level cannot be negative.')
        return value


class InventoryTransactionSerializer(serializers.ModelSerializer):
    """Serializer for inventory transactions."""
    inventory_item = serializers.PrimaryKeyRelatedField(read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(read_only=True)
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)
    performed_by_email = serializers.CharField(source='performed_by.email', read_only=True, default=None)

    class Meta:
        model = InventoryTransaction
        fields = [
            'uuid', 'inventory_item', 'inventory_item_name', 'transaction_type',
            'quantity', 'previous_stock', 'new_stock', 'reference', 'notes',
            'performed_by', 'performed_by_email', 'created_at',
        ]
        read_only_fields = ['uuid', 'previous_stock', 'new_stock', 'created_at']


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for stock adjustment operations."""
    inventory_item = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = serializers.ChoiceField(choices=InventoryTransaction.TransactionType.choices)
    notes = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def validate(self, attrs):
        transaction_type = attrs['transaction_type']
        if transaction_type in [
            InventoryTransaction.TransactionType.STOCK_OUT,
            InventoryTransaction.TransactionType.ADJUSTMENT,
            InventoryTransaction.TransactionType.DAMAGED,
        ]:
            # Stock validation happens in service
            pass
        return attrs

    def create(self, validated_data):
        from apps.inventory.models import InventoryItem

        item = InventoryItem.objects.get(uuid=validated_data['inventory_item'])
        transaction = adjust_stock(
            inventory_item=item,
            quantity=validated_data['quantity'],
            transaction_type=validated_data['transaction_type'],
            user=self.context['request'].user,
            notes=validated_data.get('notes', ''),
        )
        return transaction
