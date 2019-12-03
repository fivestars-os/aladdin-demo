FROM fivestarsos/commands-base:1.0.0

RUN apk add --no-cache \
    python3    \
    python3-dev \
    && rm -rf /var/cache/apk/*

COPY commands_app/requirements.txt ./requirements.txt
COPY redis_util redis_util
COPY elasticsearch_util elasticsearch_util

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN pip3 list --no-cache-dir --outdated

COPY commands_app/commands commands
