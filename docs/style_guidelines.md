# Style Guidelines

## Naming Conventions

| | Description | Example |
|---|---|---|
| GitHub | A repo name that contains a collection of things that work together | aladdin-demo |
| Project | Same as Git repository name | aladdin-demo |
| Dockerfiles | Named "Dockerfile" and reside within the root of associated app folder, see directory structure of more info | commands_app/Dockerfile |
| Helm Chart Name | Same as Git repository name | aladdin-demo |
| Yaml file names | Reside in appropriate app folder, \<kubenetes object type\>.yaml. If there are multiple of the same type of object in the app, then include component name. | redis/service.yaml, server/nginx.configMap.yaml, server/uwsgi.configMap.yaml |
| k8s label: project | Same as Helm Chart Name, accessed with {{ .Chart.Name }} | aladdin-demo |
| k8s label: name | Name of component in the project - should match the first part of the file name. Format: \<project name\>-\<component name\> | aladdin-demo-redis |
| k8s label: app | Same as the label "name". This is redundant and should be removed soon. However at present, Aladdin is dependent on this label. | aladdin-demo-elasticsearch |
| k8s label githash | Should be {{ .Values.deploy.imageTag }} - which is set automatically by aladdin | dab4923c44 |


## Directory Structure
### Helm Files
The recommended Helm directory structure is demonstrated below, with /helm at the root. Notably, within the /templates folder, have subdirectories for files specific to each component of the project, as well as a shared directory for shared files such as configMaps. With this subdirectory structure, we recommend one file per k8s resource named the type of that resource.

- /helm
  - /chartname
    - Chart.yaml
    - values.yaml
    - /values # One file per cluster
      - values.DEV.yaml
      - values.STAG.yaml
      - values.PROD.yaml
      - values.LOCAL.yaml
    - /templates
      - /commands
        - deploy.yaml
      - /server
        - _nginx.conf.tpl
        - nginx.configMap.yaml
        - deploy.yaml
        - service.yaml
     - /elasticsearch
        - deploy.yaml
        - service.yaml
        - elasticsearch.configmap.yaml
        - _elasticsearch.yml.tpl
      - /shared
        - configMap.yaml

## Configuration Files
All values should be stored in a values.yaml file. The templates should always reference values using helm variables. Configuration files for non-kubernetes objects, such as an nginx config file or a uwsgi config file, should be located in the template folder with a name that begins with an underscore and ends with ".tpl".

For example, below is the [\_nginx.conf.tpl](../helm/aladdin-demo/templates/server/_nginx.conf.tpl) file. 
```
{{/* Config file for nginx */}}

# Note: This define name is global, if loading multiple templates with the same name, the last
# one loaded will be used.
{{ define "nginx-config" -}}

# Specify some event configs
events {
    worker_connections 4096;
}

# Create a server that listens on the nginx port

http { 
    server {
    listen {{ .Values.app.nginx.port }};
        
        # Match incoming request uri with "/app" and forward them to the uwsgi app
        location /app {
            proxy_pass http://localhost:{{ .Values.app.uwsgi.port}};
        }
        # Match incoming request uri with "/ping" and forward them to the uwsgi app
        location /ping {
            proxy_pass http://localhost:{{ .Values.app.uwsgi.port}};
        }
        # Otherwise, nginx tries to serve static content. The only file should exist is index.html,
        # which is written by the initContainer. Get requests with "/" or "/index.html" will return
        # a short message, everything else will return 404
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
    }
}
{{ end }}
```
This creates a named template that we can reference elsewhere with the give name `nginx-config`. If you want to know more about how this works, check out [this section](https://docs.helm.sh/chart_template_guide/#declaring-and-using-templates-with-define-and-template) in the Helm Chart Template Guide.

In order to keep files modularized, we create a ConfigMap, the example below is [server/nginx.configMap.yaml](../helm/aladdin-demo/templates/server/nginx.configMap.yaml).
```yaml
# ConfigMap for nginx
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Chart.Name }}-nginx
  labels: 
    project: {{ .Chart.Name }}
    app: {{ .Chart.Name }}-nginx
    name: {{ .Chart.Name }}-nginx
    githash: {{ .Values.deploy.imageTag }}
data:
  # Make the key the desired name for the file
  # When mounted, this will create a nginx.conf file with the contents in nginx-config template
  nginx.conf: {{ include "nginx-config" . | quote }}
```
Under data, we can load the config file using the helm keyword `include`. This file can then be mounted in the deploy template for our app, [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml), giving the docker container access to it.
```yaml
volumes:
  - name: {{ .Chart.Name }}-nginx
    configMap:
      name: {{ .Chart.Name }}-nginx
```
```yaml
volumeMounts:
  - mountPath: /etc/nginx/
    name: {{ .Chart.Name }}-nginx
```
This will put /etc/nginx/nginx.conf into the docker container with that absolute path, equivalent to copying over a local nginx.conf file in a Dockerfile. 

## Git Hooks
You may wish to include git hooks in your project, such as style checks or unit tests. It is recommended that you use this [Fivestars git-hooks](https://github.com/fivestars/git-hooks) tool to structure your custom hooks for better readability. We have set up a [.githooks](../.githooks) directory and written a [pre-commit](../.githooks/pre-commit-00-style) hook that installs and runs flake8, a python style checker. Follow the instructions for installing [git-hooks](https://github.com/fivestars/git-hooks) and try to make a commit with bad python code to see it in action.
