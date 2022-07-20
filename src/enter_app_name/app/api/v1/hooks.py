from datetime import datetime
from marshmallow import ValidationError
from flask import current_app, g, jsonify, request, _request_ctx_stack
from . import api_v1
from enter_app_name.app.utils import CustomException

def add_logging_keys(response=None, status_code=None):
    logging_keys = {
        'latency': f'{(datetime.utcnow() - g.request_timestamp_start).total_seconds()}s',
        'status': status_code if status_code is not None else response.status_code,
    }
    return logging_keys


@api_v1.before_request
def set_global_variable():
    g.request_timestamp_start = datetime.utcnow()
    g.context = request.json if request.method == 'POST' else None


@api_v1.after_request
def log_request(response):
    ctx = _request_ctx_stack.top
    if response.status_code < 300:
        current_app.logger.info('after request logging', extra=add_logging_keys(response=response))
    return response


@api_v1.errorhandler(ValidationError)
def validation_error(e):
    current_app.logger.error(e, extra=add_logging_keys(status_code=400))
    return jsonify({
        'error': 'schema validation error',
        'message': e.messages
    }), 400


@api_v1.errorhandler(400)
def app_bad_request(e):
    current_app.logger.error(e)
    return jsonify({
        'error': 'bad request',
        'message': e.description,
    }), 400


@api_v1.errorhandler(500)
def app_internal_server_error(e):
    current_app.logger.error(e)
    return jsonify({
        'error': 'internal server error',
        'message': e.description
    }), 500


@api_v1.errorhandler(404)
def app_endpoint_not_found(e):
    current_app.logger.error(e)
    return jsonify({
        'error': 'resource not found',
        'message': e.description
    }), 404


@api_v1.errorhandler(CustomException)
def connection_error(e):
    current_app.logger.error(e, extra=add_logging_keys(status_code=e.status_code))
    return jsonify({
        'error': e.__class__.__name__,
        'message': e.message
    }), e.status_code