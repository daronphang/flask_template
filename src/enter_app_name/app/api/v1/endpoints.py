from flask import current_app, g, jsonify, request
from . import api_v1
from enter_app_name.app.utils import (
    binary_marshal,
    MissingKey,
    InvalidField,
    get_query_hash,
    SqlQuery
)
from enter_app_name.app.schemas import get_schema
from enter_app_name.app.tasks import tasks, ESPECMonitoring, GetFDCFailuresTask


@api_v1.route('/heartbeat', methods=['GET'])
def heartbeat():
    app_name = current_app.config['PROJECT_NAME']
    return jsonify({"response": f'{app_name} is alive'})


@api_v1.route('/testing_schema', methods=['POST'])
def testing_schema():
    get_schema('TESTING_SCHEMA').load(g.context)
    return jsonify({"response": "schema validated"})

@api_v1.route('/query/<name>', methods=['POST'])
def query(name):
    name = name.upper()
    userinfo, payload = g.context['userinfo'], g.context['payload']
    get_schema(name).load(payload)

    query_hash = get_query_hash(name)
    db_name = query_hash['db_helper'][userinfo['fab']]
    config = current_app.config[db_name] 
    
    resp = SqlQuery(
            config,
            payload,
            query_hash['sql_string'],
            query_hash['sql_helper'],
            'DEFAULT'
        ).query()

    # if need to deserialize bytes data 
    if 'pickle_helper' in query_hash:
        resp = binary_marshal(resp, query_hash['pickle_helper'])
    return jsonify({'response': resp})

@api_v1.route('/espec', methods=['POST'])
def espec():
    userinfo, payload = g.context['userinfo'], g.context['payload']
    return ESPECMonitoring(userinfo, payload).execute()

@api_v1.route('/fdc_violation', methods=['POST'])
def fdc_violation():
    userinfo, payload = g.context['userinfo'], g.context['payload']
    results = GetFDCFailuresTask(userinfo, payload, 'GET_FDC_VIOLATION').execute()
    return jsonify({'results': results})


@api_v1.route('/task/<taskname>', methods=['POST'])
def task(taskname):
    taskname = taskname.upper()
    get_schema('TASK').load(g.context)

    userinfo, payload = g.context['userinfo'], g.context['payload']
    get_schema(taskname).load(payload)

    task = getattr(tasks, 'automated_task')
    resp = task.apply_async(kwargs={'taskname': taskname, 'userinfo': userinfo, 'payload': payload})

    return jsonify({"message": f"{taskname} task registered", "task_id": resp.id}), 202


@api_v1.route('/testing_celery')
def testing_celery():
    task = getattr(tasks, 'testing_celery')
    resp = task.delay()

    # task_id = uuid()
    # resp = task.apply_async(kwargs={'taskname': 'testing'}, task_id=task_id)

    return jsonify({"task_id": resp.id})


@api_v1.route('/task_status', methods=['POST'])
def task_status():
    get_schema('CELERY_STATUS').load(g.context)
    taskname = getattr(tasks, g.context['task_name'])
    task = taskname.AsyncResult(g.context['task_id'])

    resp = {'state': task.state}

    if task.state == 'PENDING':
        pass
    elif task.state != 'FAILURE':
        if hasattr(task, 'result'):
            resp['result'] = getattr(task, 'result')
    else:
        # something went wrong in the background job
        resp['error'] = str(resp.info.__repr__())
        pass

    return jsonify(resp)


# @api_v1.route('/crud', methods=['POST'])
# def crud():
#     userinfo, payload = g.context['userinfo'], g.context['payload']

#     # Should create service to handle authorization
#     payload = CrudSchema().load(payload)
#     if payload['crud_name'] not in sql_crud_params.keys():
#         raise MissingKey(f'{payload["crud_name"]} does not exist in crud utils.')

#     entries = payload['entries']
#     operation = payload['crud_operation']

#     # Verify schema for each entry in payload to prevent SQL injection
#     if operation == 'UPDATE':
#         if isinstance(entries, dict):
#             # UPDATE operations without conditions
#             schema_handler(payload['crud_name']).load(entries)
#         elif isinstance(entries, list):
#             # UPDATE operations with conditions
#             for entry in entries:
#                 CrudUpdateCaseSchema().load(entry)
#         else:
#             raise InvalidField('Missing entries in payload.') 
#     elif operation == 'INSERT':
#         for entry in entries:
#             schema_handler(payload['crud_name']).load(entry)
#     else:
#         # Currently DELETE operations not allowed
#         raise InvalidField('CRUD operation not allowed.')

#     db_name = sql_crud_params[payload['crud_name']]['db_helper'][userinfo['fab']]
#     sql_ref = sql_crud_params[payload['crud_name']]
#     config = current_app.config[db_name]
#     if sql_crud_params[payload['crud_name']]['simple']:
#         # Single CRUD operation using simple function
#         rv = CrudOperations(config).\
#             simple_crud(payload, sql_ref)
#     else:
#         # For more complex CRUD requiring separate logic
#         rv = CrudOperations(config).\
#             get_method(payload['crud_name'])(payload, sql_ref)
#     return jsonify({'response': rv})
