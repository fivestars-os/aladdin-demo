# Using NGINX
We demonstrate running an nginx container within the same pod as the aladdin-demo-server app. Our template sets up nginx as a simple proxy server that will listen to all traffic on a port and forward it to the falcon app. We specify the nginx values in the [values.yaml](../helm/aladdin-demo/values.yaml) file.
```yaml
app:
  uwsgi:
    port: 8000
  nginx:
    use: true
    port: 80
    httpPort: 80
    httpsPort: 443
```       
Set the `use` field to `true`. This is all you need to do to see nginx work, you can verify this by restarting the app with `aladdin start`. Navigate to the aladdin-demo-server service pod in the Kubernetes dashboard and you should be able to see two containers running. Read on for how we did it. 

Since we are just using the `nginx:1.12-alpine` image without modifications, there is no need to create a separate Dockerfile for it. 

We add the nginx configuration files using the templating method described in the [Configuration Files](#configuration-files) section. We then add another container for nginx in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml).
```yaml
        - name: {{ .Chart.Name }}-nginx
          image: nginx:1.12-alpine
          ports: 
            - containerPort: {{ .Values.app.nginx.port }}
              protocol: TCP
          volumeMounts:
            - mountPath: /etc/nginx/
              name: {{ .Chart.Name }}-nginx
```
In the [server/service.yaml](../helm/aladdin-demo/templates/server/service.yaml), we expose the nginx port for the pod so that all incoming requests get routed to nginx first. 

## Nginx InitContainer
We have added a simple initContainer for nginx.

In the same [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml) file, we add a field for initContainers.
```yaml
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
  {{ end }}
```
This initContainer, which we named `install`, only needs to run a simple shell command that writes a short welcome message into a file. Therefore, it doesn't need a docker image that has any application code, it can just use a lightweight image, in this case [busybox](https://hub.docker.com/_/busybox/). 

Since the index.html file needs to be shared with the nginx container, we put it into a shared volume called `workdir`. This volume also needs to be added in the volumes field for the deployment
```yaml
      - name: workdir 
        emptyDir: {}
```
We also mounth this volume in the nginx container
```yaml
     volumeMounts:
    # mount html that should contain an index.html file written by the init container
    - mountPath: /usr/share/nginx/html
      name: workdir
```
This is all that is needed for this simple initContainer to run. We can verify that it wrote the `index.html` file by simpling running `$ curl $(minikube service --url aladdin-demo-server)`, which should return `You have reached NGINX`.
