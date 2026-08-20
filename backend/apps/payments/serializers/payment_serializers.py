from decimal import Decimal

from rest_framework import serializers

from apps.payments.models import Payment
from apps.sales.models import Sale


class SaleSummarySerializer(serializers.Serializer):
    """Minimal sale representation for nested serialization."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    receipt_number = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class ProcessedBySummarySerializer(serializers.Serializer):
    """Minimal user representation for processed_by."""
    id = serializers.UUIDField(source='uuid', read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class PaymentSerializer(serializers.ModelSerializer):
    """Full serializer for payment detail/retrieve."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    sale = SaleSummarySerializer(read_only=True)
    processed_by = ProcessedBySummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_reference', 'sale', 'amount',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'transaction_ref', 'processed_by', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PaymentListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing payments."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    sale_receipt = serializers.CharField(source='sale.receipt_number', read_only=True)
    sale_receipt_number = serializers.CharField(source='sale.receipt_number', read_only=True, default=None)
    reference_number = serializers.CharField(source='payment_reference', read_only=True)
    processed_by_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_reference', 'reference_number', 'sale_receipt', 'sale_receipt_number', 'amount',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'processed_by_name', 'created_at',
        ]
        read_only_fields = fields

    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return f'{obj.processed_by.first_name} {obj.processed_by.last_name}'
        return None


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for manually creating/recording a payment.

    NOTE: Normal payments are created automatically by the sale service.
    This is for manual payment recording or additional payments.
    """

    sale = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices)
    transaction_ref = serializers.CharField(required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_sale(self, value):
        try:
            Sale.objects.get(uuid=value)
        except Sale.DoesNotExist:
            raise serializers.ValidationError('Sale not found.')
        return value

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value
