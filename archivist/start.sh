#!/bin/sh

# Entrypoint script for backup-sync side-car for anka registry
while true; do
    python3 archive.py --action ${ACTION} --bucket ${BUCKET} --directory ${DIRECTORY} --key_id ${ACCESS_KEY} --key_secret ${SECRET_KEY} --name ${NAME} --state_file ${STATE_FILE} --endpoint_url ${ENDPOINT_URL} ${DEBUG}
    sleep ${SLEEP_INTERVAL}
done
