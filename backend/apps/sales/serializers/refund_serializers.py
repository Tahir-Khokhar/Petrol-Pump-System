from decimal import Decimal

from django.db import models as django_models
from rest_framework import serializers

from apps.accounts.models import User
from apps.sales.models import Refund, Sale


class RefundSerializer(serializers.ModelSerializer):
    """Full serializer for refund list/retrieve."""

    id = serializers.UUIDField(source='uuid', read_only=True)
    sale = serializers.UUIDField(source='sale.uuid', read_only=True)
    sale_receipt = serializers.CharField(source='sale.receipt_number', read_only=True)
    processed_by = serializers.UUIDField(source='processed_by.uuid', read_only=True)
    processed_by_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id', 'refund_number', 'sale', 'sale_receipt',
            'amount', 'reason', 'processed_by', 'processed_by_name',
            'status', 'status_display',
            'created_at', 'processed_at',
        ]
        read_only_fields = fields

    def get_processed_by_name(self, obj):
        return f'{obj.processed_by.first_name} {obj.processed_by.last_name}'


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for creating a refund."""

    sale = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.CharField()

    def validate_sale(self, value):
        try:
            sale = Sale.objects.get(uuid=value)
        except Sale.DoesNotExist:
            raise serializers.ValidationError('Sale not found.')
        if sale.status != Sale.Status.COMPLETED:
            raise serializers.ValidationError('Refunds can only be created for completed sales.')
        self._sale = sale
        return value

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Refund amount must be greater than zero.')
        # Check remaining refundable amount
        if hasattr(self, '_sale'):
            sale = self._sale
            total_refunded = sale.refunds.filter(
                status__in=[Refund.Status.PENDING, Refund.Status.APPROVED]
            ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0')
            remaining = sale.total_amount - total_refunded
            if value > remaining:
                raise serializers.ValidationError(
                    f'Refund amount exceeds remaining refundable amount. '
                    f'Remaining: {remaining}'
                )
        return value

    def validate(self, attrs):
        # Permission check: only SUPER_ADMIN/PUMP_MANAGER can create refunds
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            if user.role not in [User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER]:
                raise serializers.ValidationError(
                    'Only Super Admin or Pump Manager can create refunds.'
                )
        return attrs
