# Features

Python web application running on WSGI/Flask and Celery for background tasks.

# Setup

1. cd to root directory where requirements.txt is located
2. Activate venv.
3. pip install -r requirements.txt

## ENV

REDIS_URI=redis://localhost:6379/0
CELERY_BACKEND=redis://localhost:6379/0

## Starting Flask

1. export FLASK_APP=flask_app.py
2. export FLASK_ENV=development
3. cd to src/enter_app_name
4. flask run

## Starting Celery

1. cd to src
2. celery -A enter_app_name.celery_worker.celery worker --loglevel=info -P solo
