from flask import Blueprint

'''
Resources such as static, templates, views, error-handling are extended to app through Blueprint.
They remain in dormant state until blueprint is registered with an application.
Resources are imported below to avoid circular dependencies as resource modules will in turn
call the blueprint instance.
'''

api_v1 = Blueprint('api_v1', __name__)

from . import endpoints, hooks