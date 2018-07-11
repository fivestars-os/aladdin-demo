# Liveness and Readiness Probes

Liveness and readiness probes are a way for Kubernetes to constantly monitor your application by performing restarts or holding off traffic as needed. From the [Kubernetes documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/): 
    
> The kubelet uses liveness probes to know when to restart a Container. For example, liveness probes could catch a deadlock, where an application is running, but unable to make progress. Restarting a Container in such a state can help to make the application more available despite bugs.

> The kubelet uses readiness probes to know when a Container is ready to start accepting traffic. A Pod is considered ready when all of its Containers are ready. One use of this signal is to control which Pods are used as backends for Services. When a Pod is not ready, it is removed from Service load balancers.

The [Kubernetes documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/) does a good job of explaining how to configure these probes, and we have implemented examples as well. 

The parameters are defined in [values.yaml](../helm/aladdin-demo/values.yaml).

In the `aladdin-demo` container in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml), we make an http request to the `ping` endpoint of the aladdin-demo-server.
```yaml
# Readiness probe stops traffic to this pod if it is not ready, wait until it is ready
readinessProbe:
  httpGet:
    path: /ping
    port: {{ .Values.app.uwsgi.port }}
  initialDelaySeconds: {{ .Values.app.readiness.initalDelay }}
  periodSeconds: {{ .Values.app.readiness.period }}
# Liveness probe terminates and restarts the pod if unhealthy
livenessProbe: 
  httpGet:
    path: /ping
    port: {{ .Values.app.uwsgi.port }}
  initialDelaySeconds: {{ .Values.app.liveness.initalDelay }}
  periodSeconds: {{ .Values.app.readiness.period }}
```
For the `redis` container in [redis/deploy.yaml](../helm/aladdin-demo/templates/redis/deploy.yaml), and the `elasticsearch` container in [aladdin-demo-elasticsearch.statefulset.yaml](../helm/aladdin-demo/templates/elasticsearch/statefulset.yaml), we try to open a TCP socket at the appropriate ports.
```yaml

readinessProbe:
  tcpSocket:
    port: {{ .Values.redis.port }}
  initialDelaySeconds: {{ .Values.redis.readiness.initalDelay }}
  periodSeconds: {{ .Values.redis.readiness.period }}
livenessProbe:
  tcpSocket:
    port: {{ .Values.redis.port }}
  initialDelaySeconds: {{ .Values.redis.liveness.initalDelay }}
  periodSeconds: {{ .Values.redis.liveness.period }}
```
