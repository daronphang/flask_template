sql_query_string = {
    'instacap_auto_find_lots': {
            'sql_string':\
                '''
                SELECT
                RTRIM(FLS.lot_id) AS lot_id,
                RTRIM(FLS.design_id) AS DID,
                FLS.lot_current_qty AS qty,
                TS.trav_step_seq_no AS trav_seq_no,
                RTRIM(TRAV.trav_id) AS trav_id,
                CASE
                    WHEN FLS.scheduling_state_code IS NULL THEN RTRIM(FLS.state_code)
                    WHEN FLS.state_code = 'Waiting' THEN RTRIM(FLS.scheduling_state_code)
                    ELSE RTRIM(FLS.state_code) + ' ' + RTRIM(FLS.scheduling_state_code)
                    END AS status,
                CASE
                    WHEN UPPER(RTRIM(ATTR.lot_attr_value)) = 'YES' THEN RTRIM(FLS.lot_priority_status)+'_SFF'
                    ELSE RTRIM(FLS.lot_priority_status)
                    END AS priority,
                RTRIM(STEP.step_name) AS step,
                DAYS_INCOMING.days_incoming,
                ATTRIBUTE.corr_item_desc AS attribute

                FROM fab_lot_extraction.dbo.fab_lot_status AS FLS
                INNER JOIN (
                SELECT trav_step_seq_no, trav_step_OID, trav_OID, step_OID
                FROM traveler..trav_step 
                ) AS TS ON FLS.trav_step_OID = TS.trav_step_OID

                INNER JOIN (
                SELECT trav_OID, trav_id
                FROM traveler..traveler
                WHERE
                trav_id NOT LIKE 'PBA%'
                AND trav_id NOT LIKE 'PRB%'
                AND trav_id NOT LIKE 'PDA%'
                AND trav_id NOT LIKE 'PTA%'
                AND trav_id NOT LIKE 'PWA%'
                AND trav_id NOT LIKE 'FABOFFLOAD%'
                AND trav_state = 'ACTIVE'
                AND trav_type = 'PRODUCTION'
                ) AS TRAV ON TS.trav_OID = TRAV.trav_OID

                INNER JOIN (
                SELECT step_OID, step_name
                FROM traveler..step
                WHERE
                step_name NOT LIKE '9%'
                AND step_name NOT LIKE '8%'
                ) AS STEP ON TS.step_OID = STEP.step_OID

                LEFT JOIN (
                SELECT lot_attr_value, lot_id, corr_item_OID
                FROM fab_lot_extraction..fab_lot_attr_value
                ) AS ATTR ON ATTR.lot_id = FLS.lot_id AND ATTR.corr_item_OID = 0x89DDAEC66E050080

                LEFT JOIN (
                    SELECT 
                    LEFT(DemandGroup, 4) AS DID,
                    StepName AS step_name,
                    (
                        SELECT POTDays FROM [LinePrioritizationDSS].[dbo].[RiskScoreView]
                        WHERE
                        {fab} 
                        {demand_group}
                        {step_name}
                    ) - POTDays AS days_incoming
                    FROM [LinePrioritizationDSS].[dbo].[RiskScoreView]
                    WHERE RiskScore is NOT NULL
                    {demand_group} AND
                    StepName NOT LIKE '9%' AND
                    StepName NOT LIKE '%FOUP%' AND
                    StepName NOT LIKE '%PROBE'
                ) AS DAYS_INCOMING ON STEP.step_name = DAYS_INCOMING.step_name

                INNER JOIN (
                    SELECT FLAV.lot_id, CI.corr_item_desc
                    FROM [fab_lot_extraction].[dbo].[fab_lot_attr_value] AS FLAV
                    LEFT JOIN traveler..corr_item AS CI ON FLAV.corr_item_OID = CI.corr_item_OID 
                    WHERE 
                    {lot_attr}
                ) AS ATTRIBUTE ON ATTRIBUTE.lot_id = FLS.lot_id

                WHERE FLS.state_code NOT IN ('Complete', 'On Hold Long Term')
                AND FLS.lot_id NOT LIKE 'VL%'
                AND FLS.lot_priority_status != 'Non Prod'
                AND FLS.lot_id NOT LIKE 'TT%'
                {DID}
                {traveler}
                {quantity}
                {min_days_incoming}
                {max_days_incoming}
                ORDER BY 
                TS.trav_step_seq_no DESC
                ''',
            'sql_helper': {
                'fab': {
                    'str': 'ProcessFacilityId = {fab}'
                },
                'demand_group': {
                    'str': 'AND DemandGroup = {demand_group}'
                },
                'DID': {
                    'str': 'AND FLS.design_id = {DID}'
                },
                'step_name': {
                    'list': 'AND StepName IN {step_name}',
                    'str': 'AND StepName = {step_name}'
                },
                'traveler': {
                    'list': 'AND TRAV.trav_id IN {traveler}',
                    'str': 'AND TRAV.trav_id = {traveler}'
                },
                 'quantity': {
                    'int': 'AND FLS.lot_current_qty > {quantity}'
                },
                 'lot_attr': {
                    'list': 'corr_item_desc IN ({lot_attr})'
                },
                'min_days_incoming': {
                    'str': 'AND DAYS_INCOMING.days_incoming >= ROUND(CAST({min_days_incoming} AS FLOAT), 9)'
                },
                'max_days_incoming': {
                    'str': 'AND DAYS_INCOMING.days_incoming <= ROUND(CAST({max_days_incoming} AS FLOAT), 9)'
                },
            },
            'db_helper': {
                'f10n': 'FSMSSPROD06',
                'f10w': 'TSMSSPROD06'
            }
        },
}