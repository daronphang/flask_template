import pickle
from ..error_handlers import InvalidField, MissingKey
from .sessions import init_db_session, db_request

# functions to convert entries for sql operations
# returns placeholder string and actual values in tuple format for cursor.execute()
# Schemas to take care of sql injections for column names

class SqlQuery:
    def __init__(self, config: dict, payload: dict, sql_string: str, sql_helper: list, logger: str):
        self.payload = payload
        self.sql_string = sql_string
        self.sql_helper = sql_helper
        self._db = init_db_session(config)
        self.logger = logger

    @staticmethod
    def format_data(data: any):
        if isinstance(data, str):
            return "'" + data + "'"
        elif isinstance(data, int):
            return data
        elif isinstance(data, list):
            # return as string '45,12,32', "'john', 'kelly', 'peter'"
            results = ""
            for item in data:
                if isinstance(item, int):
                    results += str(item) + ','
                elif isinstance(item, str):
                    results += "'" + str(item) + "',"
                else:
                    raise InvalidField('sqlstringformatter does not support composite data types in lists')
            return results[:-1]
        else:
            raise InvalidField(f'sqlstringformmatter does not support {type(data)}')
    
    def format_query_string(self):
        subst_values = []

        for key in self.sql_helper:
            if key not in self.payload:
                raise MissingKey(f'missing {key} in payload')
            
            data = SqlQuery.format_data(self.payload[key])
            subst_values.append(data)
        
        return self.sql_string.format(*subst_values)
    
    @db_request
    def query(self):
        self._db.cursor.execute(self.format_query_string())
        result = self._db.cursor.fetchall()
        return result if result else 'no results returned from sql query'


class SqlCrud:
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

    # @staticmethod
    # def value_formatter(value):
    #     # To prevent SQL injection for inserting values directly to SQL string
    #     if (isinstance(value, str)):
    #         return "'{}'".format(value)
    #     if (isinstance(value, int)):
    #         return value

    # @classmethod
    # def subquery_formatter(cls, query_fields: dict, prefix: str):
    #     # entries is a list of dicts as can insert multiple rows
    #     # See payload.md for more info on format required
    #     final_query_str = ""
    #     tuple_values = () 
    #     equality_list = ['=', '>', '<', '>=', '<=']

    #     for operator, entries in query_fields.items():
    #         if operator in ['AND', 'OR']:
    #             query_str = ""
    #             for equality, nested_entries in entries.items():
    #                 if equality not in equality_list:
    #                     raise InvalidField('invalid equality provided in query_fields')
    #                 for key, value in nested_entries.items():
    #                     query_str += '{}{}%s AND '.format(key, equality)
    #                     tuple_values += (value, )
    #             final_query_str += ''.join( ' ' + operator + ' (' + query_str[:-5] + ')')
    #         elif operator == 'IN':
    #             for key, value in entries.items():
    #                 final_query_str += ' AND {} IN {}'.format(key, value).replace('[', '(').replace(']', ')')
    #         elif operator == 'BETWEEN':
    #             for key, value in entries.items(): 
    #                 final_query_str += ' AND {} BETWEEN {}'.format(key, value).replace('[', '(').replace(']', ')')
    #         else:
    #             raise InvalidField('invalid SQL operator provided in query_fields')
    #     return prefix + ' ' + final_query_str[5:], tuple_values

    # @classmethod
    # def insert_formatter(cls, table_name: str, entries: list, binary_columns: list):
    #     placeholder_str = ""
    #     column_str = ""
    #     tuple_values = () 
    #     column_order = entries[0].keys()

    #     for column in column_order:
    #         column_str += column + ','
    #     column_str = ''.join('(' + column_str[:-1] +')')
    #     for entry in entries:
    #         placeholder_str += '(' + (len(column_order) * '%s,')[:-1] + '),'
    #         for key in column_order:
    #             if key in binary_columns:
    #                 serialized_data = pickle.dumps(entry[key])
    #                 tuple_values += (serialized_data, )
    #             else:
    #                 tuple_values += (entry[key], )
    #     final_str = 'INSERT INTO {}{} VALUES{}'.format(table_name, column_str, placeholder_str[:-1])
    #     return final_str, tuple_values

    # @classmethod
    # def update_formatter(cls, table_name: str, update_entries: list or dict, query_fields: dict, binary_columns: list):
    #     """
    #     Can return two sets of sql_strings:
    #     UPDATE TABLE SET col1 = 1, col2="hello" WHERE name="John" (updating multiple columns)
    #     UPDATE TABLE 
    #         SET col1 CASE WHEN col2 = "world" AND col3=1000 THEN 1 ELSE col1 END 
    #         SET col2 CASE WHEN col3 = "red" AND col4='hi' THEN 'hello' ELSE col2 END
    #     WHERE name="John" (updating single column across multiple rows)
    #     """
    #     tuple_values = ()
    #     query_str = ""
    #     set_str = ""

    #     if isinstance(update_entries, dict):
    #         # simple UPDATE without CASE WHEN condition
    #         for key, value in update_entries.items():
    #             set_str += '{}=%s, '.format(key)
    #             if key in binary_columns:
    #                 tuple_values += (pickle.dumps(value), )
    #             else:
    #                 tuple_values += (value, )
    #     else:
    #         # CASE WHEN condition
    #         # each entry has set_column and case_entries field
    #         # each case_entry in case_entries has set_value and case_condition
    #         for set_entry in update_entries:
    #             set_entry_str = '[{}] = CASE'.format(set_entry['set_column'])
    #             case_str = ""
    #             for case_entry in set_entry['case_entries']:
    #                 # case_condition value has the same format as query_fields
    #                 case_query_str, values = cls.subquery_formatter(case_entry['case_condition'], 'WHEN')
    #                 tuple_values += values
    #                 if set_entry['set_column'] in binary_columns:
    #                     case_str += ' {} THEN {}'.format(case_query_str, pickle.dumps(case_entry['set_value']))
    #                 else:
    #                     case_str += ' {} THEN {}'.format(case_query_str, cls.value_formatter(case_entry['set_value']))
    #             set_str += set_entry_str + case_str + ' ELSE [{}] END, '.format(set_entry['set_column'])

    #     if query_fields and len(query_fields.keys()) > 0:
    #         query_str, values = cls.subquery_formatter(query_fields, 'WHERE')
    #         tuple_values += values
    #     update_str = 'UPDATE {} SET {} {}'.format(table_name, set_str[:-2], query_str)
    #     return update_str, tuple_values

    # @classmethod
    # def delete_formatter(cls, table_name: str, query_fields: dict):
    #     if len(query_fields.keys()) == 0 or query_fields is None:
    #         raise InvalidField('cannot provide empty query_fields for delete operation')
    #     query_str, values = cls.subquery_formatter(query_fields, 'WHERE')
    #     delete_str = 'DELETE FROM {} {}'.format(table_name, query_str)
    #     return delete_str, values

