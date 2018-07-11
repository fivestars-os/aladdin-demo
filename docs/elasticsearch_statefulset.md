# Elasticsearch and StatefulSets
In this example, we will set up a single node Elasticsearch cluster (note that this is NOT referring to a Kubernetes cluster, cluster is an overloaded term) and back it up with a StatefulSet and a PersistentVolume. 

This example is for a local development environment using minikube, which isn't the friendliest environment to use with elasticsearch and statefulset. As a result, there will be a few special settings that we will highlight as we go through the example.

There are quite a few components to this document, which describes in detail how the everything is set up. For a quick test to see that it works, skip down to the [Test Persistency](#test-persistency) section.

## StatefulSets
You can read more about StatefulSets in the [official Kubernetes docs](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/). The main take away is that StatefulSets manage pods in a way that is similar to Deployments, except that each pod in the StatefulSet has a unique and persistent identity, following an integral naming convention. So the first StatefulSet pod will be \<name\>-0, then \<name\>-1 and so on, rather than \<name\>-\<super long hash\> for pods managed by Deployments. This allows stable, persistent storage when used with [PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/), which are managed separately and not destroyed when a project is undeployed. We assign each pod its own PeristentVolume, so that when a StatefulSet pod is undeployed, the PersistentVolume remains, and when it is redeployed, the pod can identify its assigned PersistentVolume and mount that again, restoring all its data.

## Set up Elasticsearch backed by a StatefulSet
We start off by defining some values for elasticsearch in [values.yaml](../helm/aladdin-demo/values.yaml). 

    elasticsearch:
      create: true
      populate: true
      id: 1000
      port: 9200
      containerPort: 9200
      storage: 1Gi
      
The `id` field here refers to the uid of the `elasticsearch` user in the docker container. This value is used to change the ownership of volume mounts, which we discuss in more detail below. 

The `storage` field specifies how much storage we want to provision for the Persistent Volumes. Here it is 1 Gigabyte. 

We will use the officially supported elasticsearch docker image and define and load in the configuration for this elasticsearch image following the [Style Guidelines](style_guidelines.md). The config file is defined in [\_elasticsearch.yml.tpl](../helm/aladdin-demo/templates/elasticsearch/_elasticsearch.yml.tpl) with a few notable settings highlighted in the comments.

    {{/* Config file for elasticsearch */}}

    {{ define "elasticsearch-config" -}}
    # We are only setting up a single node
    discovery:
      zen.minimum_master_nodes: 1
    
    # Some xpack plugins that we don't need
    xpack:
      security.enabled: false
      ml.enabled: false
      graph.enabled: false
      monitoring.enabled: false
      watcher.enabled: false

    # Limit this to every 30 minutes so the logs don't get flooded with cluster info spam
    cluster.info.update.interval: "30m"

    # Change the path to write data and logs to our peristent volume mounted
    path:
      data: stateful/data
      logs: stateful/log

    # This allows other pods in the kubernetes cluster to connect to elasticsearch
    network.host: 0.0.0.0
    {{ end }}

We then create a Kubernetes Service object in [elasticsearch/service.yaml](../helm/aladdin-demo/templates/elasticsearch/service.yaml). This should look pretty simple and standard, the one **important difference** is that we need to set `spec.clusterIP: None`, making this a [Headless Service](https://kubernetes.io/docs/concepts/services-networking/service/), which is required for using with a StatefulSet. 

We create the StatefulSet object in [elasticsearch/statefulset.yaml](../helm/aladdin-demo/templates/elasticsearch/statefulset.yaml). There are a lot of components to this file, but let us take a detailed look at each one.

At the very bottom, we define the volumeClaimTemplates, which specifies what a PersistentVolume for this StatefulSet needs to be like. The Aladdin minikube should be set up such that it will dynamically provision the appropriate PeristentVolumes if they do not already exist, and the pod should be able to find the correct PersistenVolume if it has already been allocated to it. 

    volumeClaimTemplates:
    - metadata:
        name: storage
      spec:
        # Allow one node to read and write at a time
        accessModes: [ "ReadWriteOnce" ]
        storageClassName: standard
        resources:
          requests:
            storage: {{ .Values.elasticsearch.storage }}
We have requested a standard storage of 1 Gigabyte that allows one node to read and write to it at a given time. 

We take advantage of the dynamic allocation provided by minikube for provisioning this PersistentVolume. However, in a non-local environment, depending on how your Kubernetes cluster is run, it is probably better to manually create these volumes. For example, if your Kubernetes cluster is running in AWS over multiple zones, and you are using EBS volumes as your PersistentVolumes for your StatefulSet. Kubernetes cannot automatically detect which zone the EBS volume is in, so it might try to put the StatefulSet pod in a different zone, in which case it will not be able to connect to its EBS volume. This is where node affinity comes in handy as a way to specify where a pod can be placed. Though it is not used in this local example, we add a snippet of code that demonstrate how this would be set. You can read more about [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/) and [Running Kubernetes in Multiple Zones](https://kubernetes.io/docs/admin/multiple-zones/).

      {{ if .Values.affinity }}
        nodeSelector:
          affinity: {{ .Values.affinity }}
      {{ end }}

Next, let us examine the two initContainers for this stateful set. The first one increases the vm.max_map_count to satisfy the bootstrap check for elasticsearch. You can read more about this in the [official Elasticsearch docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html).

        initContainers:
      # Increase the vm.max_map_count to satisfy the bootstrap checks of elasticsearch
      - name: init-sysctl
        image: busybox
        imagePullPolicy: IfNotPresent
        command: ["sysctl", "-w", "vm.max_map_count=262144"]
        securityContext:
          privileged: true

The second initContainer should only be needed when running this in a minikube environment. We want to mount the PersistentVolume and reroute the path of elasticsearch to write into that volume. However, by default, Kubernetes will mount volumes as the root user, and Elasticsearch needs these files to be owned by the elasticsearch user. Kubernetes supports a way to change this by setting the fsGroup in the securityContext, which should change the ownership of the volumes mounted in the container to the user id defined in fsGroup. You can read more about [Configuring Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/).

     securityContext: 
       fsGroup: {{ .Vlaues.elasticsearch.id }}
       
Unfortunately, this is not currently supported in minikube. Instead, we will mount this volume into an initContainer, then run a `chown` command to change the owner of this directory to the elasticsearch user id, which should be 1000, the first non-root user id. This also changes the owner of this volume in the host, so when we mount it to our elasticsearch container, it will be under the elasticsearch user. 

        initContainers:
        - name: init-volume-chown
        image: busybox
        command: ["sh", "-c", "chown -R {{ .Values.elasticsearch.id }}:{{ .Values.elasticsearch.id }} /stateful"]
        volumeMounts:
        - name: storage
          mountPath: /stateful

Now, we can specify the elasticsearch container and mount the config file as well as the PersistentVolume.

      containers:
      - name: {{ .Chart.Name }}-elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:5.6.3
        ports:
        - containerPort: {{ .Values.elasticsearch.containerPort }}
        volumeMounts:
        - name: {{ .Chart.Name }}-elasticsearch
          # Volume mounts will override the mountPath, which in this case has a lot of other useful
          # things in it, we only want to mount elasticsearch.yml 
          mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
          # Configmaps are lists of key-value pairs, and we only need one of the keys, so we
          # specify that with a subpath 
          subPath: elasticsearch.yml
        - name: storage
          mountPath: /usr/share/elasticsearch/stateful
      volumes:
        - name: {{ .Chart.Name }}-elasticsearch
          configMap:
            name: {{ .Chart.Name }}-elasticsearch
           
At this point, the Elasticsearch cluster should be set up to correctly deploy, we just need to connect the application to it. 

## Connect with App

We create [elasticsearch_util](../app/elasticsearch_util) with the connection and population files.

We set up the connection to the elasticsearch service in [elasticsearch_connection.py](../app/elasticsearch_util/elasticsearch_connection.py). Since this is a headless service, Kubernetes will not populate any environment variables with the host and port information. We manually populate it in the configMap.

    ELASTICSEARCH_CREATE: {{ .Values.elasticsearch.create | quote }}
    ELASTICSEARCH_HOST: {{ .Chart.Name }}-elasticsearch
    ELASTICSEARCH_PORT: {{ .Values.elasticsearch.port | quote }}

This allows us to create the connection to elasticsearch.

    import os
    from elasticsearch import Elasticsearch

    es_conn = None
    if os.environ["ELASTICSEARCH_CREATE"] == "true":
        es_conn = Elasticsearch(hosts=os.environ["ELASTICSEARCH_HOST"])

We populate elasticsearch with a simple index entry in [elasticsearch_populate.py](../app/elasticsearch_util/elasticsearch_populate.py).  

    import os
    from elasticsearch_connection import es_conn

    def populateData(connection):
        connection.index(index='messages', doc_type='song', id=1, body={
            'author': 'Aladdin',
            'song': 'A Whole New World',
            'lyrics': ['I can show you the world'],
            'awesomeness': 42
        })


    if __name__ == "__main__":
        populateData(es_conn)

In [run.py](../app/run.py) we add another resource which will get the message from elasticsearch. 

    class ElasticsearchResource(object):
        def on_get(self, req, resp):
            resp.status = falcon.HTTP_200
            data = es_conn.get(index='messages', doc_type='song', id=1)
            resp.body = json.dumps(data['_source'])

    if es_conn:
      app.add_route('/app/elasticsearch', ElasticsearchResource())
 
### Application initContainers
Finally, we want to make sure that our app doesn't start before the elasticsearch service is ready. We add two initContainers to check and populate elasticsearch in [\_elasticsearch_init.tpl.yaml](../helm/aladdin-demo/templates/elasticsearch/_elasticsearch_init.tpl.yaml).

    {{ define "elasticsearch_check" -}}
    {{ if .Values.elasticsearch.create }}
    - name: {{ .Chart.Name }}-elasticsearch-check
      image: byrnedo/alpine-curl
      command:
      - 'sh'
      - '-c'
      - 'until curl {{ .Chart.Name }}-elasticsearch:{{ .Values.elasticsearch.port }}; do echo waiting for elasticsearch pod; sleep 2; done;'
    {{ end }}
    {{ end }}

    ---

    {{ define "elasticsearch_populate" -}}
    {{ if .Values.elasticsearch.create }}
    - name: {{ .Chart.Name }}-elasticsearch-populate
      image: {{ .Values.deploy.ecr }}{{ .Chart.Name }}:{{ .Values.deploy.imageTag }}
      command:
      - 'python3'
      - 'elasticsearch_util/elasticsearch_populate.py'
      envFrom:
        - configMapRef:
            name: {{ .Chart.Name }}
    {{ end }}
    {{ end }}

We include these initContainers in [server/deploy.yaml](../helm/aladdin-demo/templates/server/deploy.yaml). Since we are using persistent volume for data storage, we should only need to populate the data once, so the population initContainer is controlled by a `elasticsearch.populate` boolean specified in [values.yaml](../helm/aladdin-demo/values.yaml).

## Test Persistency
Make sure that `elasticsearch.create` and `elasticsearch.populate` are set to `true` in [values.yaml](../helm/aladdin-demo/values.yaml). Build and deploy aladdin-demo and wait until all the pods are running.

    $ aladdin build
    $ aladdin start
    $ kubectl get pods

Check that elasticsearch has been populated by curling the appropriate endpoint of the aladdin-demo service-server.

    $ curl $(minikube service --url aladdin-demo-server)/app/elasticsearch
    
    Data from ElasticSearch is {"author": "Aladdin", "song": "A Whole New World", "lyrics": ["I can show you the world"], "awesomeness": 42} 
    
Now set `elasticsearch.populate` to `false` and redeploy the app with 
   
    $ aladdin restart
Check to see if the elasticsearch still works, even though we didn't populate it this time around! You should get the same output as last time, meaning the data persisted between deployments, hooray!

For the purpose of this tutorial, we made elasticsearch.populate a toggle-able value to explicitly show what is going on. However, in a non-tutorial environment, it would not be good practice to need to change a helm variable between deploys. One possible way to handle this is to create a separate population script in a [Commands Container](./commands_container.md) that can be invoked explicited to populate data. 
