import logging

from apps.audit_logs.models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    user,
    action,
    model_name='',
    object_id='',
    description='',
    previous_value=None,
    new_value=None,
    request=None,
):
    """Create an audit log entry.

    This function uses try/except so that audit log failures never break
    the main operation. It extracts ip_address and user_agent from the
    request object if provided.
    """
    try:
        ip_address = None
        user_agent = ''
        if request is not None:
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id) if object_id else '',
            description=description,
            previous_value=previous_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        logger.exception('Failed to create audit log entry')


def _get_client_ip(request):
    """Extract client IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
