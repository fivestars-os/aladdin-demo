# Code Mounting 

You may want to mount a host directory into a container so that if code is updated on the host machine, the changes will be reflected in the container after a simple restart, instead of needing to rebuild the container image every time. 

Aladdin supports this with a `--with-mount` option, which is populated in Helm as `deploy.withMount` variable. Aladdin also populates `deploy.mountPath` to the root of your project repo. We can use these two variables to configure the correct mounts for our containers.

We have two ways of configuring mounts:

## Option 1 - RECOMMENDED

Here we need to create a project-central [persistent volume](../helm/aladdin-demo/templates/shared/nfs-mount.pv.yaml) and [persistent volume claim](../helm/aladdin-demo/templates/shared/nfs-mount.pvc.yaml) that uses nfs mounting. 
```yaml
{{ if .Values.deploy.withMount }}
apiVersion: v1
kind: PersistentVolume
metadata:
  name: {{ .Chart.Name }}-nfs-volume
spec:
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  nfs:
    server: 192.168.99.1
    path: {{ .Values.deploy.mountPath }}
{{ end }}
```

```yaml
{{ if .Values.deploy.withMount }}
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: {{ .Chart.Name }}-nfs-volume-claim
spec:
  storageClassName: standard
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
  volumeName: {{ .Chart.Name }}-nfs-volume
{{ end }}
```

Then, we can reference the claim in our container volume, and use the correct subpath in our volumeMount to create the correct container mounts like in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml). 
```yaml
        volumeMounts:
{{ if .Values.deploy.withMount }}
          - mountPath: /home
            name: {{ .Chart.Name }}-server
            subPath: app
{{ end }} # /withMount

     . . .

      volumes:
{{ if .Values.deploy.withMount }}
        - name: {{ .Chart.Name }}-server
          persistentVolumeClaim:
            claimName: {{ .Chart.Name }}-nfs-volume-claim
{{ end }} # /withMount
```

Once you have set this up correctly, you will also need to update your /etc/exports by running `echo "/Users -alldirs -mapall="$(id -u)":"$(id -g)" $(minikube ip)"| sudo tee -a /etc/exports` to give minikube access to it.  

You may also need to restart nfsd: `sudo nfsd restart`

## Option 2

Here we are mounting the app folder in the aladdin-demo directory from our host machine onto the /home path on the aladdin-demo container. 
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

This option has some issues with file consistency (e.g. you update a file on your host machine but that update doesn't show on the container). This appears to be because minikube's default file mounting is 9p. This issue has been seen on containers using alpine as their base image, but may be seen on other images as well. Unless you have verified that these issues do not occur on your project, this option is NOT recommended. 

Notice that in [app/Dockerfile](../app/Dockerfile), we copy over the code in `app` with `COPY . /home`, so everything still works when code mounting is turned off. The mounting will actually overrwrite these files, so the mounted code is used when `--with-mount` is used.
