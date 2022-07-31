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

## Docker

```console
# cd to dockerfile directory or provide filename directly
# $ docker build -t enter_app_name
# $ docker build -t enter_app_name -f /docker/Dockerfile

$ docker-compose up -d     # docker compose is using V2, which may interfere with env variables with spacing
```

### CAVEAT

If flask/celery is required to read/write files from Windows network drives, currently there is no solution to implement this. Nonetheless, it is possible to do this on Docker host.

https://medium.com/@Flashleo/mounting-windows-file-share-on-docker-container-ac930092c0a5
