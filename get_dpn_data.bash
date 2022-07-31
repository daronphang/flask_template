CUR_DATE=$(date +%Y-%m-%d)
LAST_DATE=$(date --date="-90 day" +%Y-%m-%d)
# LAST_DATE=$(date --date="-$1 day" +%Y-%m-%d)
DPN_JSON=$(cat <<EOF
{
    "userinfo": {
        "fab": "F10W",
        "username": "daronphang"
    },
    "payload": {
        "equip_ids": ["CENT7B1500", "CENT7B1300", "CENT7B1600", "CENT7B1800"],
        "start_date": "$LAST_DATE",
        "end_date": "$CUR_DATE",
        "loadport_entrance": ["Load Lock A.2", "Load Lock B.2"],
        "loadport_exit": ["Load Lock A.1", "Load Lock B.1"]
    }
}
EOF
)

curl -X POST -H "Content-Type: application/json" \
-d "$DPN_JSON" \
http://localhost:5000/api/v1/task/get_dpn_data

