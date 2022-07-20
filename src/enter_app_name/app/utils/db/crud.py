import logging
import secrets
from datetime import datetime
from .requests import (
    db_decorator,
    init_db_session,
)
from .error_handlers import InvalidField


class CrudOperations:
    def __init__(self, config):
        self.config = config
        self._db = init_db_session(config)
        
    def get_method(self, method_name):
        if hasattr(self, method_name):
            return getattr(self, method_name)        
        raise InvalidField(f'Crud method {method_name} not found.')


    # @db_decorator
    # def simple_crud(self, payload: dict, sql_ref: dict):
    #     # Generate hexadecimals of 8 bytes
    #     '0x{}'.format(secrets.token_hex(7))

    #     crud_name = payload['crud_name']
    #     crud_operation = payload['crud_operation']
    #     entries = payload['entries']
    #     query_fields = payload['query_fields']
    #     table_name = sql_ref['table_name']
    #     binary_columns = sql_ref['binary_columns']
    #     if crud_operation == 'INSERT':
    #         formatted_str, values = SqlHelper.insert_formatter(table_name, entries, binary_columns)
    #     elif crud_operation == 'UPDATE':
    #         formatted_str, values = SqlHelper.update_formatter(table_name, entries, query_fields, binary_columns)
    #     elif crud_operation == 'DELETE':
    #         formatted_str, values = SqlHelper.delete_formatter(table_name, query_fields)
    #     else:
    #         pass
    #     self._db.cursor.execute(formatted_str, values)
    #     return {'message': f'Crud operation {crud_name} success.'}
