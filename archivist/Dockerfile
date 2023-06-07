FROM python:3.10.11-alpine

RUN python3 -m ensurepip

COPY requirements.txt /requirements.txt

RUN python3 -m pip install --no-cache --upgrade -r /requirements.txt

WORKDIR /app
ADD http://trusted-cas.ubisoft.org/ca-bundle.crt /tmp/ca.crt
COPY archive.py /app/
COPY start.sh /app/

ENTRYPOINT [ "python3", "/app/archive.py" ]
