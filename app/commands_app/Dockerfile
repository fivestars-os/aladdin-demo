FROM fivestarsos/commands-base:1.0.0

COPY commands_app/requirements.txt ./requirements.txt
COPY redis_util redis_util
COPY elasticsearch_util elasticsearch_util

RUN pip install -r requirements.txt
COPY commands_app/commands commands
