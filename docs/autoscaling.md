# Autoscaling
Kubernetes provides autoscaling by CPU usage through a [HorizontalPodAutoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/). We give a simple demonstration of it in this demo project. As of Kubernetes 1.8, autoscaling by custom metrics is also available with autoscaling v2beta1. This requires setting up some extra metrics and we will not go over it in this demo.

In Kubernetes 1.8, Heapster is being deprecated and will be replaced with Metrics-Server. In order to enable autoscaling, we must ensure that metrics-server is running. Please follow instructions [here](https://kubernetes.io/docs/tasks/debug-application-cluster/core-metrics-pipeline/) to do that.

Next, we need to request cpu resources in the deployment file of the pod we are autoscaling. For each container in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml), we add
```yaml
resources:
  requests:
    cpu: 100m
``` 
This is an optional field when not worrying about autoscaling, but it is required in order for the autoscaler to monitor percentage of cpu usage. In this example, we request 100 millicpu for each container. You can read more about what cpu means and how to manage other resources [here](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/). 

Next, we create the HorizontalPodAutoscaler object in [server/hpa.yaml](../helm/aladdin-demo/templates/server/aladdin-demo.hpa.yaml).
```yaml
apiVersion: autoscaling/v2beta1
# This is an autoscaler for aladdin-demo
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Chart.Name }}-hpa
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-hpa
    app: {{ .Chart.Name }}-hpa
    githash: {{ .Values.deploy.imageTag }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1beta1
    kind: Deployment
    name: {{ .Chart.Name }}-server
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        targetAverageUtilization: 50
```
If the average cpu utilization percentage of all aladdin-demo-server pods exceeds 50%, the autoscaler will spin up new pods until the pods have less than 50% average cpu utilization. This utilization percentage is quite low for purposes of demonstration. By default, autoscaler will check on the pods every 30 seconds. This can be changed through the controller manager's `--horizontal-pod-autoscaler-sync-period` flag.

We also add a `BusyResource` in [run.py](../app/run.py), which performs a CPU intensive operation upon get request to force autoscaling.
```python
class BusyResource(object):
    def on_get(self, req, resp):
        n = 0.0001
        for i in range(1000000):
            n += sqrt(n)
        resp.body = ('busy busy...')

app = falcon.API()
app.add_route('app/busy', BusyResource())
```
Confirm that the aladdin-demo app is running. Then check the status of the autoscaler and the current number of pods with

    $ kubectl get hpa
    NAME               REFERENCE                 TARGETS    MINPODS   MAXPODS   REPLICAS   AGE
    aladdin-demo-hpa   Deployment/aladdin-demo-server   0% / 50%   1         10        1          51m
    
    $ kubectl get deployments
    NAME                        DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
    aladdin-demo-server         1         1         1            1           51m
    aladdin-demo-redis          1         1         1            1           51m
    
As expected, the CPU usage is well below the target 50%, so only one pod is needed.

Now we can manually increase the load by generating an infinite number of requests to the aladdin-demo-server service. Get the url of the aladdin demo server with
    
    $ minikube service --url aladdin-demo-server
    <a url that looks something like http://192.168.99.100:30456>

Then, in a new terminal window, run
    
    $ kubectl run -i --tty load-generator --image=busybox /bin/sh

    Hit enter for command prompt

    $ while true; do wget -q -O- <url from previous step>/app/busy; done

This should return `busy busy...` ad infinitum. Let it run for about half a minute, since the autoscaler only checks on the pod every 30 seconds, and then look at the status of the autoscaler and pods again.

    $ kubectl get hpa
    NAME               REFERENCE                 TARGETS      MINPODS   MAXPODS   REPLICAS   AGE
    aladdin-demo-hpa   Deployment/aladdin-demo-server   182% / 50%   1         10        1          51m
    
    $ kubectl get deployments
    NAME                        DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
    aladdin-demo-server         4         4         4            4           51m
    aladdin-demo-redis          1         1         1            1           51m
    
We see now that the CPU usage is much higher than the target, and as a result the autoscaler has scaled the number of desired pods up to 4 to balance the load. Hooray!

Stop the inifinite query with `ctl c` and wait for a bit. You should see the CPU drop back down and the number of pods scaled back to 1. 
