import shutil
import os
import pandas as pd
import numpy as np
import matplotlib
# by default matplotlib uses TK gui toolkit
# even when not using toolkit, matplotlib still instantiates a window that doesn't get displayed
# http://matplotlib.org/faq/howto_faq.html#matplotlib-in-a-web-application-server
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dotenv import load_dotenv
from datetime import datetime
from celery.utils.log import get_task_logger
from .. import StandardTask


load_dotenv()
logger = get_task_logger(__name__)

'''
Python script for pulling weekly SPC OOC%
Extensible to all modules if needed
outputs in HTML which can be viewed on any browser 

Requirements:
1. png-plots folder MUST be present in the cwd
'''

class PlotWeeklySPCOOC(StandardTask):
    WEEKLY_SPC_DIDS = os.environ.get('WEEKLY_SPC_DIDS').split(',')
    WEEKLY_SPC_CHARTS = os.environ.get('WEEKLY_SPC_CHARTS').split(',')
    WEEKLY_SPC_RAW_PATH = os.environ.get('WEEKLY_SPC_RAW_PATH')
    WEEKLY_SPC_PARENT_DIR = os.environ.get('WEEKLY_SPC_PARENT_DIR')

    OOC_LIMITS = {
        "CSPL": 1,
        "PML": 1.5,
        "Area": 2.5
    }
    INTERMEDIARY_OOC_DATA = []
    LAST_WW = []
    UNIQUE_WW = None

    def __init__(self, userinfo: dict, payload: dict):
        self.userinfo = userinfo
        self.payload = payload
        self.weekly_spc_areas = payload['areas']
        self.fab = userinfo['fab'].upper()

    def populate_empty_rows_algo(self, unique_ww, df):
        def binary_search():
            start = 0
            end = len(df) - 1
            mid = (end - start) // 2
            
            while start < end:
                if df.iloc[mid]['WW'] != unique_ww[mid]:
                    # before midpoint, there exists missing values
                    end = mid
                    mid = (end - start) // 2
                else:
                    # values are matched before midpoint
                    start = mid + 1
                    mid = start + (end - start) // 2
            return mid
        
        while True:
            if len(df) == len(unique_ww):
                break

            mid = binary_search()
            if df.iloc[mid]['WW'] == unique_ww[mid] and mid + 1 == len(df):
                # add remainder to df
                missing_df = pd.DataFrame({'WW': unique_ww[mid+1:], 'ooc': [np.nan] * len(unique_ww[mid+1:])})
                df = pd.concat([df, missing_df]).reset_index(drop=True)
            else:
                missing_df = pd.DataFrame({'WW': [unique_ww[mid]], 'ooc': [np.nan]})
                df = pd.concat([df.iloc[:mid], missing_df, df.iloc[mid:]]).reset_index(drop=True)

        return df

    def plot_by_fab(self, grp_df, fab, ooc_limit, ax):
        fab_df = grp_df[grp_df['Fab'] == fab]
        ooc_df = fab_df[(fab_df['ooc'] > ooc_limit) & (fab_df['WW'] == self.LAST_WW)].reset_index().to_dict('records')

        # adding ooc for f10w
        if fab == 'F10W' and len(ooc_df) > 0:
            self.INTERMEDIARY_OOC_DATA.extend(ooc_df)

        fab_df = fab_df[['WW', 'ooc']]
        if (len(fab_df) > 0):
            if (len(fab_df) < 15):
                # some work weeks 10N might have data while 10W might not, and vice versa
                # to populate missing weeks with NaN to avoid errors
                fab_df = self.populate_empty_rows_algo(self.UNIQUE_WW, fab_df)

            ax.plot(fab_df['WW'], fab_df['ooc'], label=fab, marker ='.')

            # adding text labels for each point
            for x, y in zip(fab_df['WW'], fab_df['ooc']):
                ax.annotate(text=f'{round(y, 2)}%', xy=(x, y), textcoords='offset points', xytext=(0, 5), ha='center', fontsize=7)

    
    def plot_ooc_charts(self, grp_df, area, design_id, chart_type, fab_area):
        # 15 work weeks per plot
        # each chart is based on DID and chart type i.e. B47R CSPL, B47R PML, B47R AREA

        fig = plt.figure()
        ax = fig.add_subplot()

        grp_df = grp_df[
            (grp_df['Area'] == area) &
            (grp_df['Design Id'] == design_id) &
            (grp_df['Chart Type'] == chart_type) 
        ]

        # plot f10w and f10n
        self.plot_by_fab(grp_df, 'F10N', self.OOC_LIMITS[chart_type], ax)
        self.plot_by_fab(grp_df, 'F10W', self.OOC_LIMITS[chart_type], ax)

        # adding limit horizontal line
        ax.axhline(y=self.OOC_LIMITS[chart_type], color='red')

        # rotating x-axis labels
        plt.xticks(rotation=90)

        # coloring regions between OOC horizontal line
        bottom, top = plt.ylim()
        plt.ylim(-0.2, top + 1)
        ax.axhspan(-0.2, self.OOC_LIMITS[chart_type], color='#EFF8E7')
        ax.axhspan(self.OOC_LIMITS[chart_type], top + 1, color='#FFE2D7')

        ax.legend()
        img_path = os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'png_plots', f'{fab_area}-{design_id}-{chart_type}.png')
        fig.savefig(img_path, bbox_inches='tight')
        plt.close()
        plt.close(fig)

    def generate_html_table(self, design_id_list, chart_types, fab_area):
            table_headers = '''
            <tr>
                <th>Design ID</th>
                <th>CSPL</th>
                <th>PML</th>
                <th>AREA</th>
            </tr>
            '''

            table_rows = ''

            for design_id in design_id_list:
                table_cells = f'<td>{design_id}</td>'
                for chart in chart_types:
                    img_path = os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'png_plots', f"{fab_area}-{design_id}-{chart}.png")
                    img_html = f"<img src ='{img_path}' class='img-thumbnail'>"
                    table_cells += '<td>' + img_html + '</td>'

                table_rows += '<tr>' + table_cells + '</tr>'
            
            html_table = '<table class="table table-bordered">' + table_headers + table_rows + '</table>'
            return html_table
        
    def generate_html(self, ww_date, ooc_data, snapshot_table, fab_area):
        # using boostrap CSS

        html_template = f'''
        <!DOCTYPE html>
        <html>
            <head>
                <title> Weekly SPC OOC% Snapshots </title>
                <link rel='stylesheet' href='https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css' integrity='sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh' crossorigin='anonymous'>
            </head>
            <body class='container-fluid'>
                <i>This notice is automated using Python. Thanks.</i>
                <br>
                <h3> Weekly SPC OOC% Snapshots {ww_date}</h3>
                <br>
                <h4> Failed Charts </h4>
                <br>
                {ooc_data}
                <br>
                <h4>Snapshots</h4>
                <br>
                {snapshot_table}
                <i>All information and attachments in this e-mail are Proprietary and Confidential property of Micron Technology, Inc.</i>
            </body>
        </html>
        '''

        with open(os.path.join(self.WEEKLY_SPC_PARENT_DIR, f'weekly_spc_{fab_area}.html'), 'w') as f:
            f.write(html_template)

    
    def execute(self):
        logger.info('executing PlotWeeklySPCOOC task...')

        # clear existing PNG files
        for png in os.listdir(os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'png_plots')):
            os.remove(os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'png_plots', png))

        cw = os.getcwd()
        dest_path = os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'SPCrawdata.csv')
        shutil.copyfile(self.WEEKLY_SPC_RAW_PATH, dest_path)

        raw_df = pd.read_csv(dest_path, encoding="cp1252")
        spc_df = raw_df[
            [
                "WW",
                "Fab",
                "Area",
                "Chart Type",
                "Chart Id",
                "Design Id",
                "PROCESS_TOOL",
                "STEP",
                "Uploaded #Samples",
                "Any Violation #OOC(1)",
                "Parameter",
                "OOC_Type"
            ]
        ].dropna()

        # get unique WW for x-axis plotting
        unique_ww = spc_df['WW'].unique()
        unique_ww.sort()
        first_ww = unique_ww[len(unique_ww) % 15]
        self.UNIQUE_WW = [x for x in unique_ww if x >= first_ww]
        self.LAST_WW = unique_ww[len(unique_ww) - 1]

        # filter last 15 WWs
        spc_df = spc_df[spc_df['WW'] >= first_ww]

        # perform initial groupings
        spc_groups = spc_df.groupby(['Fab', 'Area', 'Design Id', 'Chart Type', 'WW'])

        # calculate sum and ooc% for each work week and fab
        grp_df = spc_groups[['Uploaded #Samples', 'Any Violation #OOC(1)']].sum()
        grp_df['ooc'] = (grp_df['Any Violation #OOC(1)'] / grp_df['Uploaded #Samples']) * 100

        for area in self.weekly_spc_areas:
            for design_id in self.WEEKLY_SPC_DIDS:
                for chart_type in self.WEEKLY_SPC_CHARTS:
                    self.plot_ooc_charts(grp_df.reset_index(), area, design_id, chart_type, f'{self.fab}_{area}')
            
        ww_date = self.LAST_WW + ' ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # concatanenating datafarmes is slow, to append to list as dict and initialize again once ready
        for area in self.weekly_spc_areas:
            ooc_data_temp = []
            fab_area = f'{self.fab}_{area}'
            for item in self.INTERMEDIARY_OOC_DATA:
                ooc_df = spc_groups.get_group((self.fab, area, item['Design Id'], item['Chart Type'], self.LAST_WW)).drop(['WW', 'Area', 'Fab'], axis=1)
                ooc_data_temp.extend(ooc_df[ooc_df['Any Violation #OOC(1)'] > 0].to_dict('records'))
            
            # output to HTML
            ooc_data = pd.DataFrame(ooc_data_temp).reset_index(drop=True).to_html(classes='table table-striped')
            snapshot_table = self.generate_html_table(self.WEEKLY_SPC_DIDS, self.WEEKLY_SPC_CHARTS, fab_area)
            self.generate_html(ww_date, ooc_data, snapshot_table, fab_area)
        
        # deleting raw csv file to save space
        os.remove(os.path.join(self.WEEKLY_SPC_PARENT_DIR, 'SPCrawdata.csv'))

        logger.info('execution of PlotWeeklySPCOOC success')
        return 'plot weekly SPC OOC success'

                
        
        
        






