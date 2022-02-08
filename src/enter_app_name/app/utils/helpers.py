import decimal
import flask.json
import pickle

# Convert binary data types in SQL to Python objects
# Need define columns that are binary
def binary_marshal(cursor_data: list, columns: list):
    for row in cursor_data:
        for col in columns:
            row[col]= pickle.loads(row[col])
    return cursor_data


class MyJSONEncoder(flask.json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return str(obj)
        return super(MyJSONEncoder, self).default(obj)