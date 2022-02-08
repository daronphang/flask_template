from flask import current_app, g, jsonify, request
from marshmallow import base
from . import api_v1
from enter_app_name.app.utils import (
    CrudOperations,
    binary_marshal,
    MissingKey,
    InvalidField
)
from enter_app_name.app.schemas import (
    schema_handler, 
    CrudSchema,
    CrudUpdateCaseSchema,
    CrudCaseEntrySchema
)
from enter_app_name.app.tasks import tasks
from .sql_query_utils import sql_query_string
from .sql_crud_utils import sql_crud_params


@api_v1.route('/heartbeat')
def heartbeat():
    app_name = current_app.config['PROJECT_NAME']
    return jsonify({"response": f'{app_name} is alive'})


@api_v1.route('/crud', methods=['POST'])
def crud():
    userinfo, payload = g.context['userinfo'], g.context['payload']

    # Should create service to handle authorization
    payload = CrudSchema().load(payload)
    if payload['crud_name'] not in sql_crud_params.keys():
        raise MissingKey(f'{payload["crud_name"]} does not exist in crud utils.')

    entries = payload['entries']
    operation = payload['crud_operation']

    # Verify schema for each entry in payload to prevent SQL injection
    if operation == 'UPDATE':
        if isinstance(entries, dict):
            # UPDATE operations without conditions
            schema_handler(payload['crud_name']).load(entries)
        elif isinstance(entries, list):
            # UPDATE operations with conditions
            for entry in entries:
                CrudUpdateCaseSchema().load(entry)
        else:
            raise InvalidField('Missing entries in payload.') 
    elif operation == 'INSERT':
        for entry in entries:
            schema_handler(payload['crud_name']).load(entry)
    else:
        # Currently DELETE operations not allowed
        raise InvalidField('CRUD operation not allowed.')

    db_name = sql_crud_params[payload['crud_name']]['db_helper'][userinfo['fab']]
    sql_ref = sql_crud_params[payload['crud_name']]
    config = current_app.config[db_name]
    if sql_crud_params[payload['crud_name']]['simple']:
        # Single CRUD operation using simple function
        rv = CrudOperations(config).\
            simple_crud(payload, sql_ref)
    else:
        # For more complex CRUD requiring separate logic
        rv = CrudOperations(config).\
            get_method(payload['crud_name'])(payload, sql_ref)
    return jsonify({'response': rv})


@api_v1.route('/test_celery')
def celery_test():
    task = getattr(tasks, 'test_celery')
    resp = task.delay()
    return jsonify({"task_id": resp.id})


@api_v1.route('/task_status', methods=['POST'])
def task_status():
    payload = request.json
    try:
        task = getattr(tasks, payload['task_name'])
    except AttributeError as e:
        return jsonify({'response': 'tasks name does not exists'}), 404
    else:
        resp = task.AsyncResult(payload['task_id'])
        if resp.state == 'PENDING':
            response = {
                'state': resp.state,
            }
        elif resp.state != 'FAILURE':
            response = {
                'state': resp.state,
            }
            if hasattr(resp, 'result'):
                response['result'] = getattr(resp, 'result')
        else:
            # something went wrong in the background job
            response = {
                'state': resp.state,
                'error': str(resp.info.__repr__()),
            }
        return jsonify(response)
