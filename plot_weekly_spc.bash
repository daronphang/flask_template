WEEKLY_SPC_JSON=$(cat <<EOF
{
    "userinfo": {
        "fab": "F10W",
        "username": "daronphang"
    },
    "payload": {
        "areas":["DIFFUSION"]
    }
}
EOF
)

curl -X POST -H "Content-Type: application/json" \
-d "$WEEKLY_SPC_JSON" \
http://localhost:5000/api/v1/task/plot_weekly_spc_ooc

