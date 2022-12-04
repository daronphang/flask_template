import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import current_app
from celery.utils.log import get_task_logger
from enter_app_name.app.utils import SqlQuery, get_query_hash, write_to_csv


load_dotenv()
# logger = get_task_logger(__name__)

'''
http://tswfdlimits02:8090/FDCWeb/Graph/uvatrendf10.jsp
?tool_name=KOKU7B2U00_Furnace
&collection_name=FD_DF_HIKE_QUIXACE2_Furnace_StepEnd_LeakCheck_NITR_161020
&context_group=[RECIPE_NAME*%20MainRecipe/1_Product/REVJ-B680200A-R]
&window=LeakCheck
&dataitem=LeakCheckPressureMax
&statistics=Max
&last_days=7
'''


class GetFDCFailuresTask():
    PARENT_DIR = os.environ.get('FDC_VIOLATIONS_PARENT_DIR')

    def __init__(self, userinfo: dict, payload: dict, taskname: str):
        self.userinfo = userinfo
        self.payload = payload
    
    def generate_html(self, headers, fdc_violations, snapshots):
        # using boostrap CSS

        html_template = f'''
        <!DOCTYPE html>
        <html>
            <head>
                <title> Daily FDC Violation Snapshots </title>
                <link rel='stylesheet' href='https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css' integrity='sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh' crossorigin='anonymous'>
            </head>
            <body class='container-fluid'>
                <i>This notice is automated using Python. Thanks.</i>
                <br>
                <h3> Daily FDC Violation Snapshots {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</h3>
                <br>
                <h4> FDC Violations </h4>
                <br>
                <table class="table-sm">{headers}{fdc_violations}</table>
                <br>
                <h4>Snapshots</h4>
                <br>
                {snapshots}
                <i>All information and attachments in this e-mail are Proprietary and Confidential property of Micron Technology, Inc.</i>
            </body>
        </html>
        '''

        with open(os.path.join(self.PARENT_DIR, f'daily_fdc_violations.html'), 'w') as f:
            f.write(html_template)

    def execute(self):
        # fetch tools from PROD06
        query_hash = get_query_hash('GET_EQUIP_IDS')
        dbinstance = query_hash['db_helper'][self.userinfo['fab']]
        config = current_app.config[dbinstance]
        sql_results = SqlQuery(
            config,
            None,
            query_hash['sql_string'],
            query_hash['sql_helper'],
            'CELERY'
        ).query()
        tool_ids = [x['tool_id'] for x in sql_results]

        # fetch from snowflake
        query_hash = get_query_hash('GET_FDC_VIOLATION')
        dbinstance = query_hash['db_helper'][self.userinfo['fab']]
        config = current_app.config[dbinstance]
        payload = {
            'fab': 7 if self.userinfo['fab'] == 'F10W' else 10,
            'tool_ids': tool_ids,
            'yesterday': datetime.strftime(datetime.now() - timedelta(self.payload['lookback_days']), '%Y-%m-%d')
        }
        sql_results = SqlQuery(
            config,
            payload,
            query_hash['sql_string'],
            query_hash['sql_helper'],
            'CELERY'
        ).query()

        # generate HTML
        headers = ''' 
            <tr>
                <th>LOT ID</th>
                <th>DESIGN ID</th>
                <th>TOOL NAME</th>
                <th>RECIPE</th>
                <th>WINDOW</th>
                <th>DATA ITEM</th>
                <th>STATISTIC</th>
                <th>FDC LINK</th>
                <th>OCAP DATETIME</th>
            </tr>
            '''
        fdc_violations = ""
        snapshots = ""

        sql_results.sort(key=lambda x: x['TOOL_NAME'])

        for x in sql_results:
            link = 'http://tswfdlimits02:8090/FDCWeb/Graph/uvatrendf10.jsp' + \
                f"?tool_name={x['TOOL_NAME']}" + \
                    f"&collection_name={x['COLLECTION_NAME']}" + \
                        f"&context_group={x['CONTEXT_GROUP']}" + \
                            f"&window={x['WINDOW']}" + \
                                f"&dataitem={x['DATA_ITEM']}" + \
                                    f"&statistics={x['STATISTIC']}" + \
                                        '&last_days=7'

            x['FDC_LINK'] = link
            img_path = os.path.join(self.PARENT_DIR, 'snapshots', f"{x['LOT_ID']}_{x['TOOL_NAME']}_{x['WINDOW']}_{x['DATA_ITEM']}_{x['STATISTIC']}.png")
            fdc_violations += f'''
            <tr>
                <td>{x['LOT_ID']}</td>
                <td>{x['DESIGN_ID']}</td>
                <td>{x['TOOL_NAME']}</td>
                <td>{x['RECIPE_NAME']}</td>
                <td>{x['WINDOW']}</td>
                <td>{x['DATA_ITEM']}</td>
                <td>{x['STATISTIC']}</td>
                <td><a href="{link}" target="_blank">fdcweb_link</a></td>
                 <td>{x['OCAP_DATETIME']}</td>
            </tr>
            '''
            snapshots += f'''
            <h5>{x['LOT_ID']} {x['TOOL_NAME']} {x['WINDOW']} {x['DATA_ITEM']} {x['STATISTIC']}</h5>
            <br />
            <img src ="{img_path}" class='img-thumbnail'>
            <br />
            '''


        self.generate_html(headers, fdc_violations, snapshots)
        return 'success'

