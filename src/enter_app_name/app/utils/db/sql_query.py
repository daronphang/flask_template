from ..error_handlers import MissingKey

def get_query_hash(query_name):
    mapper = {
        'GET_DPN_DATA': get_dpn_data,
        'CHECK_LOT_STATUS': check_lot_status,
        'GET_SPC_VIOLATION': get_spc_violation,
        'GET_FDC_VIOLATION': get_fdc_violation,
        'GET_EQUIP_IDS': get_equip_ids,
    }

    if query_name in mapper:
        return mapper[query_name]
    raise MissingKey('invalid query name')

get_dpn_data = {
    'sql_string': '''
        SELECT
        EEH.EQUIP_ID,
        EEH.PARENT_EQUIP_ID,
        EEH.SUBSTRATE_LOCATION_ID AS LOCATION_ENTER,
        EEH_EXIT.SUBSTRATE_LOCATION_ID AS LOCATION_EXIT,
        EEH.STEP_NAME,
        EEH.RECIPE,
        EEH.DESIGN_ID,
        EEH.LOT_ID AS "LotId",
        EEH.SUBSTRATE_ID AS WAFER_SCRIBE,
        EEH.SLOT_NO
        FROM
        PROD_MFG_FAB_{0}_ODS.ET.EQUIP_EVENT_HISTORY AS EEH

        INNER JOIN (
        SELECT 
        SUBSTRATE_LOCATION_ID,
        LOT_ID,
        SUBSTRATE_ID
        FROM
        PROD_MFG_FAB_{0}_ODS.ET.EQUIP_EVENT_HISTORY
        WHERE 
        PARENT_EQUIP_ID IN ({1})
        AND EVENT_DATE_TIME >= TO_DATE({2})
        AND EVENT_DATE_TIME <= TO_DATE({3})
        AND SUBSTRATE_LOCATION_ID IN ({4})
        GROUP BY SUBSTRATE_LOCATION_ID, LOT_ID, SUBSTRATE_ID
        ) AS EEH_EXIT ON EEH_EXIT.LOT_ID = EEH.LOT_ID AND EEH_EXIT.SUBSTRATE_ID = EEH.SUBSTRATE_ID 

        WHERE 
        EEH.PARENT_EQUIP_ID IN ({1})
        AND EEH.EVENT_DATE_TIME >= TO_DATE({2})
        AND EEH.EVENT_DATE_TIME <= TO_DATE({3})
        AND EEH.SUBSTRATE_LOCATION_ID IN ({5})

        GROUP BY 
        EEH.EQUIP_ID,
        EEH.PARENT_EQUIP_ID,
        EEH.SUBSTRATE_LOCATION_ID,
        EEH_EXIT.SUBSTRATE_LOCATION_ID,
        EEH.STEP_NAME,
        EEH.RECIPE,
        EEH.DESIGN_ID,
        EEH.LOT_ID,
        EEH.SUBSTRATE_ID,
        EEH.SLOT_NO

        ORDER BY EEH.LOT_ID, EEH.SLOT_NO
    ''',
    'sql_helper': ['fab', 'equip_ids', 'start_date', 'end_date', 'loadport_exit', 'loadport_entrance'],
    'db_helper': {
        'F10W': 'SNOWFLAKE',
        'F10N': 'SNOWFLAKE',
    },
    'pickle_helper': []
}

check_lot_status = {
    # caters for lots that have been offloaded/completed as it checks against lot history instead of current seq no
    'sql_string': '''
        SELECT DISTINCT
            RTRIM(FLS.mfg_part_code) AS 'part_code',
            RTRIM(FLS.lot_id) AS 'lot_id',
            TS.trav_step_seq_no AS 'current_step_seq_no',
            RTRIM(STEP.step_name) AS 'current_step',
            RTRIM(TRAV.trav_id) AS 'trav_id',
            RTRIM(FLS.design_id) AS 'design_id',
            RTRIM(TRAV.trav_type) AS 'trav_type'
        INTO #LOTDETAILS
        FROM fab_lot_extraction..fab_lot_status FLS
        INNER JOIN  traveler..trav_step TS ON FLS.trav_step_OID = TS.trav_step_OID
        INNER JOIN  traveler..step STEP ON STEP.step_OID = TS.step_OID
        INNER JOIN traveler..traveler TRAV ON TRAV.trav_OID = TS.trav_OID
        WHERE
            FLS.lot_id = {0}
        
        SELECT DISTINCT
            LD.lot_id,
            LD.design_id,
            TRAVS.trav_id,
            LD.current_step,
            LD.current_step_seq_no,
            TRAVS.meas_step,
            TRAVS.meas_step_seq_no,
            CASE WHEN
                LH.tracked_out_datetime IS NOT NULL THEN 'PASSED'
            ELSE 'PENDING'
            END AS step_status,
            LH.tracked_in_datetime,
            LH.tracked_out_datetime,
            RTRIM(LH.step_equip_id) AS equip_id,
            RTRIM(REG.recipe_name) AS process_id,
            RTRIM(REG.program_id) as recipe_id,
            TRAVS.trav_id
        FROM fab_lot_extraction..fab_lot_hist LH 
        INNER JOIN #LOTDETAILS LD ON LD.lot_id = LH.lot_id
        INNER JOIN (
            SELECT
                RTRIM(TRAV.trav_id) as 'trav_id',
                RTRIM(TRAV.trav_title) as 'trav_title',
                RTRIM(TRAV.trav_desc) as 'trav_description',
                RTRIM(STEP.step_name) as 'meas_step',
                TS.step_OID,
                TS.trav_step_OID,
                TS.trav_step_seq_no as 'meas_step_seq_no',
                RTRIM(STEP.masking_level_code) as 'masking_level_code',
                RTRIM(TRAV.trav_state) as 'trav_state',
                RTRIM(TRAV.trav_type) as 'trav_type'  
            FROM traveler..trav_step TS
            INNER JOIN traveler..traveler TRAV ON TS.trav_OID = TRAV.trav_OID
            INNER JOIN traveler..step STEP on TS.step_OID = STEP.step_OID
            WHERE
                TRAV.trav_state = 'ACTIVE'
        ) TRAVS ON TRAVS.trav_step_OID = LH.trav_step_OID
        INNER JOIN fab_recipe..equip_group EQUIP ON EQUIP.equipment_group_name = LH.step_equip_id
        LEFT JOIN fab_recipe..process PROCESS ON PROCESS.step_OID = TRAVS.step_OID AND PROCESS.design_id = LD.design_id
        LEFT JOIN fab_recipe..process_equip_group_xref PXREF ON PXREF.process_OID = PROCESS.process_OID
        LEFT JOIN fab_recipe..recipe_equip_group REG ON REG.recipe_OID = PXREF.recipe_OID AND REG.equipment_group_OID = EQUIP.equipment_group_OID
        WHERE 
            TRAVS.meas_step IN ({1}) 
    ''',
    'sql_helper': ['lot_id', 'meas_steps'],
    'db_helper': {
        'F10W': 'TSMSSPROD06',
        'F10N': 'FSMSSPROD06',
    },
    'pickle_helper': []
}

get_spc_violation = {
    'sql_string': '''
    SELECT DISTINCT
        SLOT.EXVAL_12,
        SLOT.EXVAL_04,
        SLOT.PARAMETER_NAME,
        SLOT.SAMPLE_DATE,
        TVIOL.VIOL_COMMENT,
        VDESC.VIOL_TYPE,
        VDESC.VIOL_DESC
    FROM PROD_MFG_FAB_{0}_ODS.SPC.SAMPLES_LOT SLOT
    INNER JOIN PROD_MFG_FAB_{0}_ODS.SPC.T_EXT_SAMPLES_VIOL TVIOL ON TVIOL.SAMPLE_ID = SLOT.SAMPLE_ID
    INNER JOIN PROD_MFG_FAB_{0}_ODS.SPC.T_VIOL_DESC VDESC ON VDESC.VAL_TYPE_ID = TVIOL.VAL_TYPE_ID
    WHERE 
        SLOT.EXVAL_12 IN ({1}) 
        AND SLOT.EXVAL_04 IN ({2})
    ''',
    'sql_helper': ['fab', 'lot_ids', 'meas_steps'],
    'db_helper': {
        'F10W': 'SNOWFLAKE',
        'F10N': 'SNOWFLAKE',
    },
    'pickle_helper': []
}

get_fdc_violation = {
    'sql_string': '''
    SELECT DISTINCT
        ECAP.INSTANCE_ID,
        ECAP.SAMPLE_ID,
        ECAP.DAVAL_01 AS HIST_OID,
        RUN_DATA.TOOL_ID,
        RUN_DATA.RUN_ID,
        ECAP.EXVAL_12 AS LOT_ID,
        ECAP.EXVAL_01 AS DESIGN_ID,
        OCAP.TOOL_NAME,
        RUN_DATA.TRAVELER_STEP,
        RUN_DATA.GERM_PROCESS,
        RUN_DATA.RECIPE_NAME,
        OCAP.COLLECTION_NAME,
        OCAP.CONTEXT_GROUP,
        OCAP.ANALYSIS AS WINDOW,
        ECAP.DAVAL_15 AS DATA_ITEM,
        OCAP.STATISTIC,
        ECAP.DAVAL_08 AS OCAP_DATETIME
    FROM
        PROD_MFG_FAB_{0}_ODS.ECAP.T_SPACE2ECAP AS ECAP
        INNER JOIN PROD_MFG_FAB_{0}_ODS.FD.FD_COMMON_CONTEXT_LOT AS RUN_DATA ON RUN_DATA.FAB_LOT_HIST_OID = ECAP.DAVAL_01
        INNER JOIN PROD_MFG_FAB_{0}_ODS.FD.MT_FD_OCAP_HIST AS OCAP ON OCAP.RUN_ID = RUN_DATA.RUN_ID
    WHERE 
        ECAP.EXVAL_05 IN ({1})
        AND ECAP.DAVAL_08 >= {2}
        ORDER BY DAVAL_08 DESC
    ''',
    'sql_helper': ['fab', 'tool_ids', 'yesterday'],
    'db_helper': {
        'F10W': 'SNOWFLAKE',
        'F10N': 'SNOWFLAKE',
    },
    'pickle_helper': []
}

get_equip_ids = {
    'sql_string': '''
    SELECT 
        RTRIM(equip_id) AS tool_id
    FROM 
        [equip_tracking_DSS].[dbo].[equipment]
    WHERE
        equip_status = 'ACTIVE'
        AND mfg_facility_OID = 0x7F5156E2400A9854 
        AND mfg_area_OID = 0x2D512D4EEE3A4A42
        AND RTRIM(equip_type_id) IN ('VANTAGE_RTP', 'VANTAGE_ISSG_CHM', 'CENTURA_DPNPLS_CHM', 'CENTURA_DPNRTP_CHM', 'INDY_LPOXO2RICH', 'INDYPLS_LPOXO2RICH', 'INDYPLS_RADOX', 'INDY_ATMOXANNL', 'QU_ALDOX', 'QUIXACE2_NITR', 'QUIXACE2_POLY', 'QUIXACE2_TEOS')
    ORDER BY equip_type_id, equip_id
    ''',
    'sql_helper': [],
    'db_helper': {
        'F10W': 'TSMSSPROD06',
        'F10N': 'FSMSSPROD06',
    },
    'pickle_helper': []
}