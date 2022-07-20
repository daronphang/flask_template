from flask import current_app, Flask, jsonify
from flask_moment import Moment
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from celery import Celery
from enter_app_name.config import config, CeleryConfig


origins = ['http://127.0.0.1:4200', 'http://localhost:4200']

cors = CORS()
mm = Marshmallow()
db = SQLAlchemy()
moment = Moment()
celery = Celery(
    __name__,
    backend=CeleryConfig.backend_result,
    broker=CeleryConfig.broker_url
)


'''
Application factory for application package. \
Delays creation of an app by moving it into a factory function that can be \
explicitly invoked from script and apply configuration changes.
'''

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name]) # load config from python module
    config[config_name].init_app(app)

    # Exposes all resources matching /* to CORS and allows Content-Type header
    # For cookies, need implement CSRF as additional security measure
    cors.init_app(app, resources={r"/*": {"origins": origins, "support_credentials": True}})
    mm.init_app(app)
    db.init_app(app)
    celery.conf.update(app.config)
    update_celery(app, celery)

    from enter_app_name.app.api.v1 import api_v1 as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    register_app_errors(app)

    return app


def update_celery(app, celery):
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def register_app_errors(app):
    @app.errorhandler(400)
    def app_bad_request(e):
        current_app.logger.error(e)
        return jsonify({
            'error': 'bad request',
            'message': e.description,
        }), 400


    @app.errorhandler(500)
    def app_internal_server_error(e):
        current_app.logger.error(e)
        return jsonify({
            'error': 'internal server error',
            'message': e.description
        }), 500


    @app.errorhandler(404)
    def app_endpoint_not_found(e):
        current_app.logger.error(e)
        return jsonify({
            'error': 'resource not found',
            'message': e.description
        }), 404