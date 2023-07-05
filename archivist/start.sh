#!/bin/sh

# Entrypoint script for backup-sync side-car for anka registry
while true; do
    python3 archive.py ${DEBUG} ${ACTION} \
        --directory ${DIRECTORY} \
        --state_file ${STATE_FILE} \
        --name ${NAME} \
        --key_id ${ACCESS_KEY} \
        --key_secret ${SECRET_KEY} \
        --bucket ${BUCKET} \
        --endpoint_url ${ENDPOINT_URL}
    sleep ${SLEEP_INTERVAL}
done
