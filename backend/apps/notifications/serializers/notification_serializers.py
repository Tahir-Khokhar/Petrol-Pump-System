from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'uuid', 'user', 'title', 'message', 'notification_type',
            'is_read', 'related_object_model', 'related_object_id', 'created_at',
        ]
        read_only_fields = fields


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'uuid', 'title', 'message', 'notification_type', 'is_read', 'created_at',
        ]
        read_only_fields = fields
