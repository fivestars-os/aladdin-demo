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
