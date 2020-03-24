# Code Mounting 

You may want to mount a host directory into a container so that if code is updated on the host machine, the changes will be reflected in the container. This way you won't need to rebuild the container image every time. 

Aladdin supports this with a `--with-mount` option, which is populated in Helm as `deploy.withMount` variable. Aladdin also populates `deploy.mountPath` to the root of your project repo. We can use these two variables to configure the correct mounts for our containers.

Here is how we recommend you configure your mounts:

In this code snippet, we are mounting the app folder in the aladdin-demo directory from our host machine onto the /home path on the aladdin-demo container. 
```yaml
        volumeMounts:
{{ if .Values.deploy.withMount }}
          - mountPath: /home
            name: {{ .Chart.Name }}-server
{{ end }} # /withMount

     . . .

      volumes:
{{ if .Values.deploy.withMount }}
        - name: {{ .Chart.Name }}-server
          hostPath:
            path: {{ .Values.deploy.mountPath }}/app
{{ end }} 
```

Notice that in [app/Dockerfile](../app/Dockerfile), we copy over the code in `app` with `COPY . /home`, so everything still works when code mounting is turned off. The mounting will actually overrwrite these files, so the mounted code is used when `--with-mount` is used.
