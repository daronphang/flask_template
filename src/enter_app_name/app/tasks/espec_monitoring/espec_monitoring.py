import shutil
import os
import logging
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
from enter_app_name.app.utils import curry
# from celery.utils.log import get_task_logger
# from dotenv import load_dotenv
# from .. import StandardTask

# load_dotenv()
logger = logging.getLogger(__name__)
# logger = get_task_logger(__name__)

'''
Raw Data: \\f10-pi-08\ParamMonitor\Extracts\Data
Traffic Light: \\tssvm2general-241-lif1\pee300mm_PI\Critical param traffic light monitoring\param auto\Param auto in use\Traffic Light Automation
Trendanator: \\tssvm2general-241-lif1\pee300mm_PI\H_IMFS_Secure_FAB10_PIE_Process_Integration_Reports\Trends
Targets: \\fswvmrpt16\ParamMonitor

Overall MS = | overall Mean - Mean Target | / Sigma Target
Overall SR = overall Sigma / Sigma Target

30days = 

Steps:
1. Get past 7WW based on current date
2. Add WW to each row
2. Group by WW


Limits: 
How do you determine the limit? 
Will this be something changed consistently or fixed?
Will we have upper and lower limit?

Tasks:
1. Add Y3 plot for each parameter
2. For B47R, plot 10N MS and SR - 10W MS and SR (check if 30days or 1 week)
'''

# TODO: some registers have targets that are 0 and hence, unable to calculate MS and SR: 01785, 02097, 01767, 09580

class ESPECMonitoring():
    PARENT_DIR = os.environ.get('ESPEC_MONITORING_PARENT_DIR')
    RAW_DIR = os.environ.get('ESPEC_MONITORING_RAW_DIR')
    TARGET_DIR = os.environ.get('ESPEC_MONITORING_TARGET_DIR')

    REGISTER_LIMITS = {
        'MS': {
            '01590': 0.4,
            '01783': 0.2,
            '03401': 0.4,
            '03501': 0.2,
            '05292': 0.9,
            '08874': 0.3,
            '06095': 0.2,
            '04625': 0.8,
            '06711': 0.2,
            '05819': 0.5,
        }
    }

    REGISTERS = [
        '::WaferData::(00821) RES_CS_POLY-W0_1X1X1_MUX:Ohms/Cnt(MEDIAN)',
        '::WaferData::(01590) RES_4T_W0_0.88X15030_MUX:mOhms/Sq(MEDIAN)',
        '::WaferData::(01783) RES_CS_POLY-W0_1X1_KELVIN-MUX:Ohms/Cnt(MEDIAN)',
        '::WaferData::(01785) RES_CS_W1-W2_1X1X1_KELVIN-MUX:Ohms/Cnt(MEDIAN)',
        '::WaferData::(01767) RES_4T_LPW_255X1275_MUX:Ohms/Sq(MEDIAN)',
        '::WaferData::(02467) CACC_CAP_PSLV_AGED:fF/um^2(MEDIAN)',
        '::WaferData::(03401) TINV_CAP_PSHV_AGED:A(MEDIAN)',
        '::WaferData::(03501) TINV2_CAP_PLV_AGED:A(MEDIAN)',
        '::WaferData::(04130) QBD_CAP_NLV_AGED-GIANT:C/cm^2(MEDIAN)',
        '::WaferData::(04131) QBD_CAP_NSHVM_AGED-GIANT:C/cm^2(MEDIAN)',
        '::WaferData::(04132) QBD_CAP_PLV_AGED-GIANT:C/cm^2(MEDIAN)',
        '::WaferData::(04137) QBD_CAP_NSLV_AGED:C/cm^2(MEDIAN)',
        '::WaferData::(04625) IDS_TR_NSLV_200X3:uA/um(MEDIAN)',
        '::WaferData::(05292) IDS_TR_NLV_200X2.9:uA/um(MEDIAN)',
        '::WaferData::(05819) IOFFD+2.4VD_TR_NLV_3.2X2.9X1400_DDC-SRC1:pA/um(MEDIAN)',
        '::WaferData::(05853) VT_TR_PSLV_200X2.5:V(MEDIAN)',
        '::WaferData::(05985) VTCCSAT-1.8VD_TR_PSLV_200X2.5:V(MEDIAN)',
        '::WaferData::(06095) IDS_TR_PSLV_200X2.5:uA/um(MEDIAN)',
        '::WaferData::(06096) IDS_TR_PSLV_200X2.2:uA/um(MEDIAN)',
        '::WaferData::(06711) SVT_TR_NSHVSD_24X18.5_GLOBAL5K:V(MEDIAN)',
        '::WaferData::(07390) VT+0VFP_TR_NSHVSD_24X18.5_GLOBAL5K:V(MEDIAN)',
        '::WaferData::(08874) IDS_TR_PLV_200X2.4:uA/um(MEDIAN)',
        '::WaferData::(09580) MIN-BV_TR_HVISO_5X25X167_BLDVR:V(MEDIAN)'
        '::WaferData::(09550) VTCCSAT_TR_LVMUX_6.4X7.52_BLDVR-BLC-SRC:V(MEDIAN)'
    ]

    FILE_PATHS_HASHMAP = {
        'B47R': {
            'RAW': "B47R29param.csv",
            'TARGET': "B47R_29ParamTargets.csv"
        },
        'B47T': {
            'RAW': "B47T29param.csv",
            'TARGET': "B47T_29ParamTargets.csv"
        },
        'N48R': {
            'RAW': "N48R29param.csv",
            'TARGET': "N48R_29ParamTargets.csv"
        },
    }

    def __init__(self, userinfo: dict, payload: dict):
        self.userinfo = userinfo
        self.payload = payload
        self.WWs = []
        self.design_ids = payload['design_ids']
        self.register_targets_df = None

    def standardize_WW(self, date_string, workweek):
        # 11/18/2022 3:18, 11/18/2022 10:48, 11/18/2022 19:15
        local_date = date_string.split(' ')[0]
        year = local_date.split('/')[2]

        if workweek == 1 and local_date.split('/')[0] == '12':
            year += 1
        
        return f'{year}-{str(workweek).zfill(2)}'
    
    def get_lookback_WWs(self):
        # TODO: verify WW if it is int or string ('1' or '01')
        year, week, weekday = datetime.now().isocalendar()
        if weekday > 4:
            week += 1
        for i in range(self.payload['lookbackWeekCount'], 0, -1):
            if week - i > 0:
                self.WWs.append(f'{year}-{week-i}')
            else:
                self.WWs.append(f'{year-1}-{53+week-i}')
    
    def read_and_filter_raw_data(self, design_id):
        df = pd.read_csv(os.path.join(self.RAW_DIR, self.FILE_PATHS_HASHMAP[design_id]['RAW']), encoding="cp1252")
        df = df.rename(columns={'0000-00 START LOT START::LotData::ProcessFacilityId': 'FAB'})
        df['WW'] = df.apply(lambda row: self.standardize_WW(row['9100-29 INLINE PARAM::WaferData::EndDateTime'], row['WW']), axis=1)

        # retrieve columns if exist
        col_hashmap = {}
        registers = []
        for col in df.columns:
            col_hashmap[col] = True
        
        for reg in self.REGISTERS:
            if '9100-29 INLINE PARAM' + reg in col_hashmap:
                registers.append('9100-29 INLINE PARAM' + reg)
            elif '9100-29 INLINE PARAM 2' + reg in col_hashmap:
                registers.append('9100-29 INLINE PARAM 2' + reg)

        df = df[registers + ['WW', 'FAB']]
        df = df[df['WW'].isin(self.WWs)]
        df.fillna(0)
        return df, registers

    def agg_by_grouping(self, df, grouping):
       agg_df = df.groupby(grouping, as_index=False).agg(['mean', 'std'])
       agg_df.columns = ['_'.join(col) for col in agg_df.columns.values]
       return agg_df.reset_index()

    def get_register_targets(self, design_id):
        df = pd.read_csv(os.path.join(self.TARGET_DIR, self.FILE_PATHS_HASHMAP[design_id]['TARGET']), encoding="cp1252")
        return df[['Register', 'Name', 'Target', 'Sigma']]
    
    def plot_subplot(self, targets, x_values, ax, np_arr, statistic, title, label, limit):
        if np_arr.size == 0:
            logger.warning(f'empty numpy array, skipping {title}')
            return
        elif statistic == 'MS':
            calc_fn = np.vectorize(lambda x: abs(x - targets['Target']) / targets['Sigma'])
        elif statistic == 'SR':
            calc_fn = np.vectorize(lambda x: x / targets['Sigma'])
        else:
            logger.warning(f'invalid statistic passed, {title}')
            return
        
        y_values = calc_fn(np_arr)
        ax.plot(x_values, y_values, marker ='.', label=label)

        # add limits
        if limit is not None:
            ax.axhline(limit)

        # adding text labels for each point
        for x, y in zip(x_values, y_values):
            ax.annotate(text=f'{"{:.2f}".format(y)}', xy=(x, y), textcoords='offset points', xytext=(0, 5), ha='center', fontsize=7)
        # adding labels
        ax.set_title(title)
        # add legend if required
        if label is not None:
            ax.legend()
       
    def plot_charts(self, register_targets_df, overall_agg_df, fab_agg_df, design_id, register):
        # get register targets by ID i.e. 06096
        s_idx = register.find('(')
        reg_id = register[s_idx+1:s_idx+6]
        targets = register_targets_df[register_targets_df['Register'] == int(reg_id)].to_dict('records')
        if not targets or targets is None:
            logger.warning(f'target for {design_id} and {register} does not exist, skipping')
            return
        else:
            targets = targets[0]
        
        if targets['Target'] * targets['Sigma'] == 0:
            logger.warning(f'not divisible by zero, skipping for {design_id} {register}')
            return ""
        
        if reg_id in self.REGISTER_LIMITS['MS']:
            limit = self.REGISTER_LIMITS['MS'][reg_id]
        else:
            limit = None

        # to plot total of 4 charts, overall (MS and SR) and Fab-Fab (MS and SR)
        # all charts are plotted onto a single canvas, stacked horizontally for MS and MR, vertically for different categories
        # 2D numpy array
        fig, ((ax1, ax2),(ax3, ax4)) = plt.subplots(2, 2, figsize=(6,3)) 

        curry_subplot = curry(self.plot_subplot, 8)
        curry_subplot(targets, overall_agg_df['WW'])

        curry_subplot(ax1, overall_agg_df[f'{register}_mean'].to_numpy(), 'MS', 'MS (Overall)', None, limit)
        curry_subplot(ax2, overall_agg_df[f'{register}_std'].to_numpy(), 'SR', 'SR (Overall)', None, None)
        curry_subplot(ax3, fab_agg_df[fab_agg_df['FAB'] == 'FAB 10'][f'{register}_mean'].to_numpy(), 'MS', 'MS (By Fab)', 'FAB10', limit)
        curry_subplot(ax3, fab_agg_df[fab_agg_df['FAB'] == 'FAB 7'][f'{register}_mean'].to_numpy(), 'MS', 'MS (By Fab)', 'FAB7', None)
        curry_subplot(ax4, fab_agg_df[fab_agg_df['FAB'] == 'FAB 10'][f'{register}_std'].to_numpy(), 'SR', 'SR (By Fab)', 'FAB10', None)
        curry_subplot(ax4, fab_agg_df[fab_agg_df['FAB'] == 'FAB 7'][f'{register}_std'].to_numpy(), 'SR', 'SR (By Fab)', 'FAB7', None)

        curry_subplot('GARBAGE_COLLECT')
        
        fig.set_figheight(14)
        fig.set_figwidth(16)

        # rotate x-axis labels for each subplot
        for ax in fig.axes:
            plt.sca(ax)
            plt.xticks(rotation=90)
  
        # saving charts
        img_path = os.path.join(self.PARENT_DIR, 'snapshots', f'{design_id}_{reg_id}.png')
        fig.savefig(img_path, bbox_inches='tight')
        plt.close()
        return img_path

    def generate_html(self, dynamic_html):
        # using boostrap CSS

        html_template = f'''
        <!DOCTYPE html>
        <html>
            <head>
                <title> ESPEC Monitoring 29IP </title>
                <link rel='stylesheet' href='https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css' integrity='sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh' crossorigin='anonymous'>
            </head>
            <body class='container-fluid'>
                <i>This notice is automated using Python. Thanks.</i>
                <br>
                <h3> ESPEC Monitoring 29IP ({datetime.now().strftime('%m/%d/%Y %I:%M:%S%p')})</h3>
                <br>
                {dynamic_html}
                <i>All information and attachments in this e-mail are Proprietary and Confidential property of Micron Technology, Inc.</i>
            </body>
        </html>
        '''

        with open(os.path.join(self.PARENT_DIR, f'espec_monitoring_29IP.html'), 'w') as f:
            f.write(html_template)
        
    def execute(self):
        dynamic_html = ""

        # clear existing PNG files
        for png in os.listdir(os.path.join(self.PARENT_DIR, 'snapshots')):
            os.remove(os.path.join(self.PARENT_DIR, 'snapshots', png))
        
        self.get_lookback_WWs()
    
        # loop through registers for each DID and generate HTML content
        for design_id in self.design_ids:
            table_rows = ""
            headings = ""
            matplot_charts = ""
            y3_charts = ""

            df, registers = self.read_and_filter_raw_data(design_id)
            overall_agg_df = self.agg_by_grouping(df, ['WW'])
            fab_agg_df = self.agg_by_grouping(df, ['WW', 'FAB'])
            register_targets_df = self.get_register_targets(design_id)

            for idx, register in enumerate(registers):
                img_path = self.plot_charts(register_targets_df, overall_agg_df, fab_agg_df, design_id, register)
                s_idx = register.find('(')
                y3_img_path = os.path.join(self.PARENT_DIR, 'y3_charts', f'{design_id}_{register[s_idx+1:s_idx+6]}.bmp')

                # generate dynamic HTML table
                # two registers per row i.e. two columns
                headings += f"<td>{register}</td>"
                matplot_charts += f"<td><img src ='{img_path}' class='img-thumbnail'></td>"
                y3_charts += f"<td><img src ='{y3_img_path}' class='img-thumbnail'></td>"
                
                if idx % 2 != 0 or idx == len(registers) - 1:
                    table_rows += f"<tr style='text-align: center; font-weight: bold;'>{headings}</tr><tr>{matplot_charts}</tr><tr>{y3_charts}</tr>"
                    headings = ""
                    matplot_charts = ""
                    y3_charts = ""
            
            dynamic_html += f'<h4>{design_id}</h4><br><table class="table table-bordered table-striped">{table_rows}</table><br>'
        
        self.generate_html(dynamic_html)

        return 'success'
