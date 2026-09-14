from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None or isinstance(response.data, dict) and 'error' in response.data:
        return response

    detail = response.data
    message = detail.get('detail') if isinstance(detail, dict) else detail
    response.data = {
        'error': {
            'code': exc.__class__.__name__.upper(),
            'message': str(message),
            'details': detail,
        }
    }
    return response
