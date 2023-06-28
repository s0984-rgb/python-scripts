FROM python:3.10.11-alpine

RUN python3 -m ensurepip

WORKDIR /app
COPY . /app/

RUN python3 -m pip install --no-cache --upgrade -r /app/requirements.txt

ENTRYPOINT [ "python3", "/app/archivist.py" ]
