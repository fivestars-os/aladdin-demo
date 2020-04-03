#!/bin/sh

# Pass SIGTERM on to uwsgi and wait for it to exit
trap 'kill -TERM $(jobs -p) &>/dev/null && wait' TERM

if $APM_ENABLED; then
    echo "APM tracing enabled: $DATADOG_SERVICE_NAME"
    # start our server through ddtrace-run, which will allow us to see apm tracing in datadog
    ddtrace-run uwsgi /config/uwsgi.yaml &
else
    echo "APM tracing disabled"
    uwsgi /config/uwsgi.yaml &
fi

# Backgrounding uwsgi and then waiting on it allow us (instead of just calling it without &)
# allows us to wake up in response to SIGTERM and run our signal handler (which would otherwise
# wait to run until uwsgi had exited)
wait
