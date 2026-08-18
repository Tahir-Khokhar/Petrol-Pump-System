from rest_framework import serializers

from apps.audit_logs.models import AuditLog


class UserSummarySerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.CharField()


class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'uuid', 'user', 'action', 'model_name', 'object_id',
            'description', 'previous_value', 'new_value',
            'ip_address', 'user_agent', 'created_at',
        ]
        read_only_fields = fields


class AuditLogListSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'uuid', 'user', 'user_email', 'action', 'model_name', 'object_id',
            'description', 'ip_address', 'created_at',
        ]
        read_only_fields = fields
