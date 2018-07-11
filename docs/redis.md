# Using Redis
We demonstrate running a second pod with a redis container and having aladdin-demo-server retreive data from it upon request. Our template creates a redis server, then creates a connection to it in the falcon app using the redis-py client. Similar to the nginx example, we specify redis values in [values.yaml](../helm/aladdin-demo/values.yaml).
```yaml
redis:
  create: false
  port: 6379
  containerPort: 6379
```   
Changing the `create` field to `true` and restarting the app with `aladdin restart` will show you redis at work. **TODO** Currently redis startup takes about 130 seconds, so wait a bit and then verify that redis is working by curling the redis endpoint of the app. 
    
    $ curl $(minikube service --url aladdin-demo-server)/app/redis 
    
This should return `I can show you the world from Redis`. In the Kubernetes dashboard, you should also see two pods, one named `aladdin-demo` and the other named `aladdin-demo-redis`. We will detail how everything fits together below. 

We are using the `redis:2.8` image with no modifications, so a Dockerfile is not needed. Eventually our python app will be needing information about redis, so we can store this information as key-value pairs the [configMap](../helm/aladdin-demo/templates/shared/configMap.yaml).
```yaml
data:
  REDIS_CREATE: {{ .Values.redis.create | quote }}
```

In [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml), we load the data from the [configMap](../helm/aladdin-demo/templates/shared/configMap.yaml) as environment variables. This allows the python app to access the redis information through `os.environ["KEY"]`, as we will see later. 
```yaml
envFrom:
  - configMapRef:
      name: {{ .Chart.Name }}
```
Since we are putting redis in its own pod, it needs its own deployment and service objects. Following our naming convention for helm charts, we create [redis/deploy.yaml](../helm/aladdin-demo/templates/redis/deploy.yaml) and [redis/service.yaml](../helm/aladdin-demo/templates/redis/service.yaml).

With these files, the redis pod will successfully deploy in Kubernetes. Now we just need to connect it with the python app. We create a simple connection in [redis_connection.py](../app/redis_util/redis_connection.py) called `redis_conn`.
```python
import redis
import os

redis_conn = None
if os.environ["REDIS_CREATE"] == "true":
    redis_conn = redis.StrictRedis(
                host=os.environ["ALADDIN_DEMO_REDIS_SERVICE_HOST"],
                port=os.environ["ALADDIN_DEMO_REDIS_SERVICE_PORT"],
            )
```
We populate redis with a simple message in [redis_populate.py](../app/redis_util/redis_populate.py). This code is excuted by an initContainer, which we will explain in more detail below.
```python
from redis_connection import redis_conn

if __name__ == "__main__":
    redis_conn.set('msg', '\n I can show you the world from Redis\n \n')
```
In [run.py](../app/run.py), we define a redis resource and add it to the falcon api.
```python
import falcon
from redis_util.redis_connection import redis_conn

class RedisResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        msg = redis_conn.get('msg')
        resp.body = (msg)

app = falcon.API()

if redis_conn:
    app.add_route('/app/redis', RedisResource())
```
## Redis InitContainer
For this demo app, there is only one line of data in our redis database, so doing the population in the app will not cause any noticable problems. However, it is more likely the case that your database will have a much larger dataset. In this case, we can leverage initContainers to ensure redis is fully populated and ready to serve before starting up the main application. This avoids errors in the case where the app is running and receiving requests but the database is not, resulting in returned errors. By blocking the app, anyone that tries to connect to the app's endpoint will be told `Waiting, endpoint for service is not ready yet...`, and will retry after a short sleep instead of returning an error.

We demonstrate this by having two initContainers. The first one checks to see that the redis service is running, and the second one populates the database. 

Similar to the nginx initContainer, all this requires is a definition of a name, image, and command. In order to keep files cleaner, we put the definitions in [\_redis_init.tpl](../helm/aladdin-demo/templates/redis/_redis_init.tpl), using the same `define` method for templates. 
```yaml
{{ define "redis_check" -}}
{{ if .Values.redis.create }}
- name: {{ .Chart.Name }}-redis-check
  image: busybox
  command:
  - 'sh'
  - '-c'
  - 'until nslookup {{ .Chart.Name }}-redis; do echo waiting for redis pod; sleep 2; done;'
{{ end }}
{{ end }}

---

{{ define "redis_populate" -}}
{{ if .Values.redis.create }}
- name: {{ .Chart.Name }}-redis-populate
  image: {{ .Values.deploy.ecr }}{{ .Chart.Name }}:{{ .Values.deploy.imageTag }}
  command:
  - 'python3'
  - 'redis_util/redis_populate.py'
  envFrom:
    - configMapRef:
        name: {{ .Chart.Name }}
{{ end }}
{{ end }}
```
Then, in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml), we `include` them, which will simply copy and paste the code defined earlier in the following location. We need to manually indent it to ensure it is valid yaml.
```yaml    
initContainers:
# initContainer that checks that redis contianer is up and running
{{ include "redis_check" . | indent 6 }}
# initContainer that populates redis, only runs if the previous one terminates successfully
{{ include "redis_populate" . | indent 6 }}
```
These initContainers will run before the pod starts, so by the time the app starts, it redis will already have been populated with the correct data.
