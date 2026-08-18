from rest_framework import serializers
from django.utils import timezone

from apps.expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """Full serializer for expenses."""
    employee_email = serializers.EmailField(source='employee.email', read_only=True, default=None)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, default=None)

    class Meta:
        model = Expense
        fields = [
            'uuid', 'category', 'amount', 'description', 'employee',
            'employee_email', 'expense_date', 'payment_method',
            'receipt_reference', 'notes', 'created_by', 'created_by_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class ExpenseListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for expenses."""
    employee_email = serializers.EmailField(source='employee.email', read_only=True, default=None)
    employee_name = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, default=None)
    receipt_number = serializers.CharField(source='receipt_reference', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'uuid', 'category', 'amount', 'description', 'employee',
            'employee_email', 'employee_name', 'expense_date', 'payment_method',
            'receipt_number', 'created_by_email', 'created_at',
        ]

    def get_employee_name(self, obj):
        return f'{obj.created_by.first_name} {obj.created_by.last_name}'.strip()


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating expenses."""
    class Meta:
        model = Expense
        fields = [
            'category', 'amount', 'description', 'employee',
            'expense_date', 'payment_method', 'receipt_reference', 'notes',
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate_expense_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError('Expense date cannot be in the future.')
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
