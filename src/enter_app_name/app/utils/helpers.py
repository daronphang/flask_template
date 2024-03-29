import decimal
import flask.json
import pickle
import logging
import time
import csv
from celery.utils.log import get_task_logger

logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)


class MyJSONEncoder(flask.json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return str(obj)
        return super(MyJSONEncoder, self).default(obj)


def exponential_backoff(exc_to_check, logger: str, retries=3, delay=3, backoff=2):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger_map = {
                'DEFAULT': logger,
                'CELERY': celery_logger
            }

            retry, exp_delay = retries, delay
            while retry > 0:
                try:
                    return f(*args, **kwargs)
                except exc_to_check as e:
                    retry_msg = f'{e.message}. Retrying in {exp_delay} seconds... Retries left: {retry}'
                    logger_map[logger].warning(retry_msg)
                    time.sleep(exp_delay)
                    retry -= 1
                    exp_delay *= backoff
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Convert binary data types in SQL to Python objects
# Need define columns that are binary
def binary_marshal(cursor_data: list, columns: list):
    for row in cursor_data:
        for col in columns:
            if row[col]:
                row[col]= pickle.loads(row[col])
    return cursor_data

def curry(fn, arg_count: int):
    # tuple of arguments must match with arg_count
    # concern of memory leak if not cleared
    closure_args = []

    def curried(*args):
        nonlocal closure_args
        if len(closure_args)+len(args) >= arg_count:
            return fn(*closure_args,*args)
        elif args[0] == 'GARBAGE_COLLECT':
            # garbage collect
            del closure_args
            return
        closure_args += args
        return curried
    return curried

def write_to_csv(filename: str, data: list):
    # data is a list of dictionaries
    fieldnames = data[0].keys()

    with open(filename, 'w', newline='') as f:
        write = csv.DictWriter(f, fieldnames)
        write.writeheader()
        write.writerows(data)

def composite_fn(*fns):
    # takes a tuple of functions, and processes them from left to right
    # result from each function is passed on to the next
    def compose(f,g):
        return lambda x: g(f(x))    # result from f(x) is passed to g as arg
    return reduce(compose, fns, lambda x : x)