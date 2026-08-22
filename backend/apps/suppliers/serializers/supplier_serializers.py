import re

from rest_framework import serializers

from apps.suppliers.models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    """Full serializer for supplier detail/retrieve."""
    id = serializers.UUIDField(source='uuid', read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'uuid', 'company_name', 'contact_person', 'phone', 'email',
            'address', 'tax_number', 'bank_details', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class SupplierListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""
    id = serializers.UUIDField(source='uuid', read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'company_name', 'contact_person', 'phone', 'email',
            'tax_number', 'status', 'created_at',
        ]


class SupplierCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a supplier."""

    class Meta:
        model = Supplier
        fields = [
            'company_name', 'contact_person', 'phone', 'email',
            'address', 'tax_number', 'bank_details', 'status',
        ]

    def validate_company_name(self, value):
        """Validate company_name uniqueness for active suppliers."""
        if value:
            qs = Supplier.objects.filter(
                company_name__iexact=value,
                status=Supplier.Status.ACTIVE,
            )
            if self.instance:
                qs = qs.exclude(uuid=self.instance.uuid)
            if qs.exists():
                raise serializers.ValidationError(
                    'An active supplier with this company name already exists.',
                    code='unique',
                )
        return value

    def validate_phone(self, value):
        """Validate phone format (allows digits, spaces, dashes, +, parentheses)."""
        if value:
            pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(pattern, value):
                raise serializers.ValidationError(
                    'Phone number format is invalid. Use digits, spaces, dashes, +, or parentheses.',
                    code='invalid_phone',
                )
        return value


class SupplierUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a supplier (all fields optional)."""

    class Meta:
        model = Supplier
        fields = [
            'company_name', 'contact_person', 'phone', 'email',
            'address', 'tax_number', 'bank_details', 'status',
        ]
        extra_kwargs = {
            field: {'required': False}
            for field in fields
        }

    def validate_company_name(self, value):
        """Validate company_name uniqueness for active suppliers on update."""
        if value:
            qs = Supplier.objects.filter(
                company_name__iexact=value,
                status=Supplier.Status.ACTIVE,
            )
            if self.instance:
                qs = qs.exclude(uuid=self.instance.uuid)
            if qs.exists():
                raise serializers.ValidationError(
                    'An active supplier with this company name already exists.',
                    code='unique',
                )
        return value

    def validate_phone(self, value):
        """Validate phone format."""
        if value:
            pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(pattern, value):
                raise serializers.ValidationError(
                    'Phone number format is invalid. Use digits, spaces, dashes, +, or parentheses.',
                    code='invalid_phone',
                )
        return value
