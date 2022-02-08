from datetime import datetime
from marshmallow import ValidationError
from flask import current_app, g, jsonify, request, _request_ctx_stack
from . import api_v1
from app.utils import CustomException


@api_v1.before_request
def set_global_variable():
    g.request_timestamp = datetime.utcnow()
    g.context = request.json if request.json else None


@api_v1.after_request
def log_request(response):
    ctx = _request_ctx_stack.top
    request_duration = (datetime.utcnow() - g.request_timestamp)\
        .total_seconds()
    data = {
        'url': ctx.request.url,
        'method': ctx.request.method,
        'server_name': ctx.app.name,
        'blueprint': ctx.request.blueprint,
        'view_args': ctx.request.view_args,
        'status': response.status_code,
        'speed': float(request_duration),
        'payload': g.context,
        'service_name': current_app.config['PROJECT_NAME']
    }
    current_app.logger.info(f'after request logging: {data}')
    return response


@api_v1.errorhandler(ValidationError)
def validation_error(e):
    current_app.logger.error(e)
    return jsonify({
        'error': 'schema validation error',
        'message': e.messages
    }), 400


@api_v1.errorhandler(CustomException)
def connection_error(e):
    current_app.logger.error(e)
    return jsonify({
        'error': e.__class__.__name__,
        'message': e.message
    }), e.status_code