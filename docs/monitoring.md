# Monitoring
It is always a good idea to set up monitoring for your applications. We will give some guidance on how we set up some of our monitoring at Fivestars, but feel to use the monitoring systems that best suit your needs.

## APM Tracing with Datadog
We set up the datadog agent as a daemonset on our clusters, and create services that allow other pods to send data to the datadog agent. We include the apikey in the datadog agent, so the application does not need to keep track of apikeys, it just needs to know the name of the service.

Make sure you have a datadog agent running on your cluster.

To set up APM tracing, the app will need to set the following environment variables, which is done in the values files and set in the environment through configmaps. 

```yaml
DATADOG_SERVICE_NAME: #Name of your application
DATADOG_ENV: #Name of the environment the application is running on
DATADOG_TRACE_AGENT_HOSTNAME: #Name of the datadog agent service
```
It may also be useful to limit what environments you want to enable apm tracing on by default. For the demo project, we use the `APM_ENABLED` flag and disable apm tracing by default on local, dev, and staging environments. 

We must also start the application through `ddtrace` in the [entrypoint.sh](../app/entrypoint.sh), Datadog's python tracing client. You may also need to read through the [datadog python trace document](http://pypi.datadoghq.com/trace/docs/) to ensure the frameworks your app is using is up to date and compatible with `ddtrace`. Make sure you have it installed in [reqirements.txt](../app/requirements.txt). 

```bash
if $APM_ENABLED; then
    echo "APM tracing enabled: $DATADOG_SERVICE_NAME"
    # start our server through ddtrace-run, which will allow us to see apm tracing in datadog
    ddtrace-run uwsgi /config/uwsgi.yaml
else
    echo "APM tracing disabled"
    uwsgi /config/uwsgi.yaml
fi
```

With these changes, the application should start sending trace logs to datadog, which can be seen in the apm tab on the datadog website.
