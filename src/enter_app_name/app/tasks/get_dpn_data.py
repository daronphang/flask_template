import os
from dotenv import load_dotenv
from flask import current_app
from enter_app_name.app.utils import SqlQuery, sql_query_hash, write_to_csv

load_dotenv()


class GetDPNDataTask:
    def __init__(self, userinfo: dict, payload: dict, taskname: str):
        self.userinfo = userinfo
        self.payload = payload
        self.query_hash = sql_query_hash[taskname]
        dbinstance = self.query_hash['db_helper'][userinfo['fab']]
        self.config = current_app.config[dbinstance]
        
        
    def execute(self):
        # fetch from snowflake
        fab = 7 if self.userinfo['fab'] == 'F10W' else 10
        self.payload['fab'] = fab
        sql_results = SqlQuery(
            self.config,
            self.payload,
            self.query_hash['sql_string'],
            self.query_hash['sql_helper'],
            'DEFAULT'
        ).query()

        write_to_csv(os.path.join(os.environ.get('DPN_DATA_DIRECTORY'), 'dpn_loadport_data.csv'), sql_results)
        return 'write to csv success'

