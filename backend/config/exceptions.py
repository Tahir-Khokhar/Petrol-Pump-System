from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
        extra={
            'request': context.get('request'),
            'view': context.get('view').__class__.__name__ if context.get('view') else None,
        },
    )
        return Response(
            {
                'success': False,
                'message': 'An unexpected error occurred. Please try again later.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(response.data, dict):
        data = {'success': False}

        if 'detail' in response.data:
            data['message'] = response.data['detail']
        elif 'non_field_errors' in response.data:
            data['message'] = '; '.join(response.data['non_field_errors'])
        else:
            data['message'] = 'Validation error.'
            data['errors'] = response.data

        response.data = data
    elif isinstance(response.data, list):
        response.data = {
            'success': False,
            'message': '; '.join(str(e) for e in response.data),
        }
    else:
        response.data = {
            'success': False,
            'message': str(response.data),
        }

    return response
