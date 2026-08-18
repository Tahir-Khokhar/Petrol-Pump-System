from rest_framework import status, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.audit_logs.filters import AuditLogFilter
from apps.audit_logs.models import AuditLog
from apps.audit_logs.permissions import CanViewAuditLogs
from apps.audit_logs.serializers.audit_log_serializers import AuditLogSerializer, AuditLogListSerializer


@extend_schema_view(
    list=extend_schema(
        summary='List audit logs',
        description='Retrieve a paginated list of audit logs. Only SUPER_ADMIN and PUMP_MANAGER can access.',
        responses={200: AuditLogListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary='Retrieve audit log',
        description='Retrieve detailed information about a specific audit log entry.',
        responses={200: AuditLogSerializer},
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for audit logs. No create/update/delete via API."""

    queryset = AuditLog.objects.select_related('user').order_by('-created_at')
    permission_classes = [CanViewAuditLogs]
    filterset_class = AuditLogFilter
    search_fields = ['description']
    ordering_fields = ['created_at', 'action', 'model_name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AuditLogSerializer
        return AuditLogListSerializer

    def get_paginated_response(self, data):
        """Override to wrap pagination in standard response format."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': 'Audit logs retrieved successfully.',
            'data': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'results': data,
            },
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Audit logs retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
