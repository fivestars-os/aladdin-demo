# Aladdin Demo

## What is Aladdin Demo?
The aladdin-demo is a template project that will demonstrate how to write an aladdin-compatible project. If you are creating a new project from scratch, it is recommended that you start with this template, which already provides simple integration with uWSGI, Falcon, NGINX, Redis, and Elasticsearch. This document will provide a detailed walkthrough of aladdin-demo, explaining each component and best practice guidelines in project development.

## Building the Aladdin-demo Project
Pre-requisite: if you are here, it is assumed that you've already installed and set up Aladdin (https://github.com/fivestars-os/aladdin)

### Setup

You can jump right in to aladdin-demo to see Aladdin in action. You will need to change the values files to match your cluster names (e.g. renaming values.XYZ.yaml files in the helm/aladdin-demo/values folder to values.{YOUR CLUSTER NAME}.yaml). 

    $ git clone git@github.com:fivestars-os/aladdin-demo.git
    $ cd aladdin-demo
    $ aladdin build
    $ aladdin start

This is all you need to do to install aladdin-demo locally! Confirm that it is working by curling the app endpoint and see what aladdin-demo has to say. 

    $ curl $(minikube service --url aladdin-demo-server)/app
    
      I can show you the world 

We will go over how the base project is working with Aladdin. See the [Useful and Important Documentation](#useful-and-important-documentation) section for a detailed guide on each of the extra integrated components.

## Aladdin Files
These components are required for aladdin to run a project

### lamp.json
This file is essentially providing aladdin with a roadmap to your project. The [lamp.json](lamp.json) file for this demo project looks like this.
```json
{
    "name": "aladdin-demo",
    "build_docker": "./build/build_docker.sh",
    "helm_chart": "./helm/aladdin-demo",
    "docker_images": [
        "aladdin-demo",
        "aladdin-demo-commands"
    ]
}
```
You will need to specify a name, which should be a project name that adheres to the naming conventions defined in [Style Guidelines](docs/style_guidelines#naming-conventions.md). This name should be used everywhere.

The `build_docker` field should point to where your docker building script is.

The `helm_chart` field should point to your project's Helm directory. See [below](#helm) for more details about what should go in this directory.

The `docker_images` field should contain a list of the names of the images your project will be using. Only the custom images that you build need to be specified. External images that are used directly, such as busybox, redis, or nginx, do not need to be in this list.

### Docker
Your project will need to be running in Docker containers, which only require a Dockerfile and a build script. It may be beneficial to get a basic understanding of Docker from the [Official Get Started Documentation](https://docs.docker.com/get-started/). 

This is the [Dockerfile](app/Dockerfile). It starts from a base image of `alpine:3.6` and installs everything in `requirements.txt`, copies over the necessary code, and adds an entrypoint, which is the command that runs when the container starts up. The comments in the code should explain each command.
```dockerfile
FROM alpine:3.6

# install python and pip with apk package manager
RUN apk -Uuv add python py-pip

# uwsgi in particular requires a lot of packages to install, delete them afterwards
RUN apk add --no-cache \
        gettext \
        python3 \
        build-base \
        linux-headers \
        python3-dev

# copies requirements.txt to the docker container
ADD requirements.txt requirements.txt

# Install requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# clean up environment by deleting extra packages
RUN apk del \
        build-base \
        linux-headers \
        python3-dev

# specify the directory that CMD executes from
WORKDIR /home

# copy over the directory into docker container with given path
COPY . /home

# Create unprivileged user account
RUN addgroup aladdin-user && \
    adduser -SD -G aladdin-user aladdin-user

# Switch to the unpriveleged user account
USER aladdin-user

# run the application with uwsgi once the container has been created
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
```
We create and use an unpriviledged user account called aladdin-user, as it is best practice to not run uwsgi as root.

The [requirements.txt](app/requirements.txt) simply specify certain versions of libraries that are required for the app to run. This is what we have in our requirements file.

    ddtrace==0.11.0
    elasticsearch>=5.0.5,<6.0.0
    redis==2.10.6
    falcon==1.4.1
    uwsgi==2.0.15

The docker build script should just call `docker build` on the desired Dockerfiles. We have included some helper functions that make the process easier. Our [build_docker.sh](build/build_docker.sh) looks like this.
```shell
#!/usr/bin/env bash

echo "Building aladdin-demo docker image (~30 seconds)"

BUILD_PATH="$(cd "$(dirname "$0")"; pwd)"
PROJ_ROOT="$(cd "$BUILD_PATH/.." ; pwd)"

docker_build() {
    typeset name="$1" dockerfile="$2" context="$3"
    TAG="$name:${HASH}"
    docker build -t $TAG -f $dockerfile $context
}
cd "$PROJ_ROOT"

docker_build "aladdin-demo" "app/Dockerfile" "app"

docker_build "aladdin-demo-commands" "app/commands_app/Dockerfile" "app"
```
### Helm 
Helm charts are the main way to specify objects to create in Kubernetes. It is highly recommended that you take a look at the official [Helm Chart Template Guide](https://docs.helm.sh/chart_template_guide/), especially if you are unfamiliar with Kubernetes or Helm. It is well written and provides a good overview of what helm is capable of, as well as detailed documentation of sytax. It will help you understand the helm charts in this demo better and allow you to follow along with greater ease. We will also be referencing specific sections of the Helm guide in other parts of our documentation.

#### Chart.yaml
The Helm charts for this project are located in [helm/aladdin-demo](helm/aladdin-demo). The root of this directory should contain [Chart.yaml](helm/aladdin-demo/chart.yaml), a simple file that should define the name and version of the project. This name will be used a lot in other files, and can be accessed through {{ .Chart.Name }}.

    apiVersion: v1
    description: A Helm chart for Kubernetes
    name: aladdin-demo
    version: 0.1.0

#### Values.yaml
Also in the root of the Helm directory is a [values.yaml](helm/aladdin-demo/values.yaml) file. This file defines a number of default values that may be overwritten by other environment specific values files.
```yaml
# Application configuration
app:
  uwsgi:
    port: 8000
  nginx:
    use: true
    port: 80
    httpPort: 80
    httpsPort: 443

deploy:
  # number of seconds for the containers to perform a graceful shutdown, after which it is voilently terminated
  terminationGracePeriod: 50
  replicas: 1

redis:
  create: true
  port: 6379
  containerPort: 6379
```
The values in this file can be accessed in other files through {{ .Values.\<value\> }}. For example, {{ .Values.app.uwsgi.port }} will resolve to 8000.

The environment can be specified through Aladdin, which will use the appropriate values file to deploy the project. It is common practice to have multiple environments, such as local, dev, staging, and prod, which may require different parameters to be set. In our example, we will use KDEV, KSTAG, and KPROD as three different Kubernetes clusters, and we put their respective values files in a separate [values](../helm/aladdin-demo/values) folder that Aladdin can find when running on that cluster. See the aladdin documentation for more detail on how to run in non-local environments.
#### Templates
The [templates](helm/aladdin-demo/templates/) directory is for template files. For our base project, we just need a Kubernetes Deployment object and Service object.

In [server/deploy.yaml](helm/aladdin-demo/templates/server/deploy.yaml) we specify the Deployment object for the aladdin-demo app. The file contains a lot of different components for the integration of various other tools, but for the basic app, the deployment should look something like this. There are a lot of extra things in here, such as initContainers. You may need to rip out things you don't need if you are starting from this. 
```yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: {{ .Chart.Name }}-server
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-server
    app: {{ .Chart.Name }}-server
    githash: {{ .Values.deploy.imageTag }}
spec:
  selector:
    matchLabels:
      app: {{ .Chart.Name }}-server
  replicas: {{ .Values.deploy.replicas }}
  strategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        project: {{ .Chart.Name }}
        name: {{ .Chart.Name }}-server
        app: {{ .Chart.Name }}-server
    spec:
      # Number of seconds for the containers to perform a graceful shutdown,
      # after which it is voilently terminated. This defaults to 30s, most apps may not need to change it
      terminationGracePeriodSeconds: {{ .Values.deploy.terminationGracePeriod }}
      # Only schedule pods on nodes with the affinity: critical-datadog-apm label
      {{ if .Values.affinity }}
      nodeSelector:
        affinity: {{ .Values.affinity }}
      {{ end }}
      containers:
############# aladdin-demo-uwsgi app container ####
## This is a container that runs the falcon aladdin-demo app with uwsgi server
#############################################
      - name: {{ .Chart.Name }}-uwsgi
        # Docker image for this container
        image: {{ .Values.deploy.ecr }}{{ .Chart.Name }}:{{ .Values.deploy.imageTag }}
        workingDir: /home
        # Container port that is being exposed within the node
        ports:
        - containerPort: {{ .Values.app.uwsgi.port }}
          protocol: TCP
        # Mount the configuration file into the docker container
        volumeMounts:
          # Absolute path is used here
          - mountPath: /config/uwsgi.yaml
            name: {{ .Chart.Name }}-uwsgi
            subPath: uwsgi.yaml
{{ if .Values.deploy.withMount }}
          - mountPath: /home
            name: {{ .Chart.Name }}-server
            subPath: app
{{ end }} # /withMount
        envFrom:
          # Load the data from configMap into the runtime environment
          # This allows us to use os.environ["KEY"] to look up variables
          - configMapRef:
              name: {{ .Chart.Name }}
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
          limits:
            cpu: 200m
            memory: 200Mi
        {{ if .Values.app.readiness.use }}
        # Readiness probe stops traffic to this pod if it is not ready, wait until it is ready
        readinessProbe:
          httpGet:
            path: /ping
            port: {{ .Values.app.uwsgi.port }}
          initialDelaySeconds: {{ .Values.app.readiness.initialDelay }}
          periodSeconds: {{ .Values.app.readiness.period }}
        {{ end }} # /app.readiness.use
        # Liveness probe terminates and restarts the pod if unhealthy
        {{ if .Values.app.liveness.use }}
        livenessProbe: 
          httpGet:
            path: /ping
            port: {{ .Values.app.uwsgi.port }}
          initialDelaySeconds: {{ .Values.app.liveness.initialDelay }}
          periodSeconds: {{ .Values.app.readiness.period }}
        {{ end }} # /app.liveness.use
############# nginx server container ########
## This is a container for an nginx server
#############################################
{{ if .Values.app.nginx.use }}
      # nginx container, only gets created if the app.nginx.use field is true in values.yaml
      - name: {{ .Chart.Name }}-nginx
        image: nginx:1.12-alpine
        ports: 
          - containerPort: {{ .Values.app.nginx.port }}
            protocol: TCP
        volumeMounts:
          - mountPath: /etc/nginx/
            name: {{ .Chart.Name }}-nginx
          # mount html that should contain an index.html file written by the init container
          - mountPath: /usr/share/nginx/html
            name: workdir
        envFrom:
          - configMapRef:
              name: {{ .Chart.Name }}
        resources:
          requests:
            cpu: 100m
{{ end }}
############# init container ################
## initContainers must run and successfully exit before the pod can start. If it fails, K8s
## will restart the initContainers until it is successful. 
## You can have multiple initContainers, they will execute one by one in order
#############################################
      initContainers:
{{ if .Values.app.nginx.use }}
      # writes a short message into index.html into a mounted volume file shared by nginx
      # this will be the default page that shows up when sending get requests to nginx that
      # are not forwarded to uWSGI
      - name: install
        image: busybox
        command: ["sh", "-c", "printf '\n You have reached NGINX \n \n' > /work-dir/index.html"]
        volumeMounts:
        - name: workdir
          mountPath: "/work-dir"
{{ end }} # /nginx.use
{{ if .Values.redis.create }}
        # initContainer that checks that redis contianer is up and running
{{ include "redis_check" . | indent 6 }}
        # initContainer that populates redis, only runs if the previous one terminates successfully
{{ include "redis_populate" . | indent 6 }}
{{ end }} # /redis.create
        # initContainers that check that elasticsearch container is up and running, populates it if it is
{{ if .Values.elasticsearch.create }}
{{ include "elasticsearch_check" . | indent 6 }}
{{ if .Values.elasticsearch.populate }}
{{ include "elasticsearch_populate" . | indent 6}}
{{ end }} # /elasticsearch.populate
{{ end }} # /elasticsearch.create
############# end of containers #############
      # Specify volumes that will be mounted in the containers
      volumes:
        - name: {{ .Chart.Name }}-nginx
          configMap:
            name: {{ .Chart.Name }}-nginx
        - name: {{ .Chart.Name }}-uwsgi
          configMap:
            name: {{ .Chart.Name }}-uwsgi
{{ if .Values.app.nginx.use }}
        - name: workdir 
          emptyDir: {}
{{ end }}
{{ if .Values.deploy.withMount }}
        - name: {{ .Chart.Name }}-server
          persistentVolumeClaim:
            claimName: {{ .Chart.Name }}-nfs-volume-claim
{{ end }} # /withMount
```
We specify the image in spec.template.spec.containers. If using a custom built docker image, the name should be the same name as what it is named in the build docker script. The `{{ .Values.deploy.ecr }}` and `{{ .Values.deploy.imageTag }}` are automatically populated by Aladdin. 

We also mount the configmap for uwsgi using the cofiguration file guidelines specified in [Style Guidelines](docs/style_guidelines.md#configuration-files).

In [aladdin-demo.service](helm/aladdin-demo/templates/server/service.yaml) we specify the Service object for aladdin-demo.
```yaml
apiVersion: v1
kind: Service
metadata: 
  name: {{ .Chart.Name }}-server
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-server
    app: {{ .Chart.Name }}-server
    githash: {{ .Values.deploy.imageTag }}
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: {{.Values.service.certificateArn | quote}}
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: http
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
spec:
  # Aladdin will fill this in as NodePort which will expose itself to things outside of the cluster
  # This is to highlight difference between public and private service types, and to only use
  # public service types when it truly should be public
  type: {{ .Values.service.publicServiceType | quote }}
  ports:
  - name: http
    port: {{ .Values.app.nginx.httpPort }}
{{ if .Values.app.nginx.use }}
    targetPort: {{ .Values.app.nginx.port }}
{{ else }}
    targetPort: {{ .Values.app.uwsgi.port }}
{{ end }}
  - name: https
    port: {{ .Values.app.nginx.httpsPort }}
{{ if .Values.app.nginx.use }}
    targetPort: {{ .Values.app.nginx.port }}
{{ else }}
    targetPort: {{ .Values.app.uwsgi.port }}
{{ end }}
  selector:
    # Get the aladdin-demo-server deployment configuration from sever/deploy.yaml
    name: {{ .Chart.Name }}-server
```
This file should be much simpler compared to the deployment file, since it just sets up a port, in this case a public NodePort and then through a selector, hooks up the deployment object so that it serves this port. We have also enabled ssl in this example, with the `{{.Values.service.certificateArn | quote}}` set via aladdin. 

## Falcon and uWSGI
We set up a very simple Falcon API app that is backed by uWSGI. The falcon app is defined in [run.py](app/run.py) and it simply adds a few endpoints to the api. 
```python
import falcon
import json
from math import sqrt
from redis_util.redis_connection import redis_conn
from elasticsearch_util.elasticsearch_connection import es_conn


class BaseResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = '\n I can show you the world \n \n'


class RedisResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        msg = redis_conn.get('msg')
        resp.body = msg


class BusyResource(object):
    # A computation intense resource to demonstrate autoscaling
    def on_get(self, req, resp):
        n = 0.0001
        for i in range(1000000):
            n += sqrt(n)
        resp.body = 'busy busy...'


class PingResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = ''


class ElasticsearchResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        data = es_conn.get(index='messages', doc_type='song', id=1)
        msg = '\nData from ElasticSearch is {} \n \n'.format(json.dumps(data['_source']))
        resp.body = msg


app = falcon.API()

if redis_conn:
    app.add_route('/app/redis', RedisResource())
if es_conn:
    app.add_route('/app/elasticsearch', ElasticsearchResource())
app.add_route('/app', BaseResource())
app.add_route('/app/busy', BusyResource())
app.add_route('/ping', PingResource())
```
Our code is in `run.py` and we named our falcon API object `app`, so we specify those things in the uWSGI config file in [\_uwsgi.yaml.tpl](helm/aladdin-demo/templates/server/_uwsgi.yaml.tpl).
```yaml
{{/* Config file for uwsgi */}}

# Note: This define name is global, if loading multiple templates with the same name, the last
# one loaded will be used.
{{ define "uwsgi-config" -}}
uwsgi:
  uid: aladdin-user
  gid: aladdin-user
  master: true
  http: :{{ .Values.app.uwsgi.port }}
  processes: {{ .Values.app.uwsgi.processes }}
  wsgi-file: run.py
  callable: app
{{ end }}
```
With these components in place, we have now created a simple project with Aladdin! For documentation on how we integrated other components, look below at [Useful and Important Documentation](#useful-and-important-documentation)!

## Useful and Important Documentation
- [Style Guidelines](docs/style_guidelines.md)
- [Debugging Tips and Tricks](docs/debugging_tip_and_tricks.md)
- [Code Mounting](docs/code_mounting.md)
- [Commands Containers](docs/commands_containers.md)
- [InitContainers](docs/init_containers.md)
- [Liveness and Readiness Probes](docs/probes.md)
- [Using Nginx](docs/nginx.md)
- [Using Redis](docs/redis.md)
- [Autoscaling](docs/autoscaling.md)
- [Using Elasticsearch with StatefulSet](docs/elasticsearch_statefulset.md)

