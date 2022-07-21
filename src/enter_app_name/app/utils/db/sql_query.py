sql_query_hash = {
    'GET_DPN_DATA': {
        'sql_string': '''
     

            SELECT
            EEH.EQUIP_ID,
            EEH.PARENT_EQUIP_ID,
            EEH.SUBSTRATE_LOCATION_ID AS LOCATION_ENTER,
            EEH_EXIT.SUBSTRATE_LOCATION_ID AS LOCATION_EXIT,
            EEH.STEP_NAME,
            EEH.RECIPE,
            EEH.DESIGN_ID,
            EEH.LOT_ID,
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
}