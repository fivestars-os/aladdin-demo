#!/bin/sh

if $APM_ENABLED; then
    echo "APM tracing enabled: $DATADOG_SERVICE_NAME"
    # start server through ddtrace-run, which will produce apm tracing in datadog
    ddtrace-run uwsgi --pcre-jit --yaml /config/uwsgi.yaml
else
    echo "APM tracing disabled"
    uwsgi --pcre-jit --yaml /config/uwsgi.yaml
fi
