# Container Resource Management
Containers on a Pod are scheduled on node in your cluster, which has a limited amount of CPU and memory. If you do not specify how much resource you expect your pod to need to use, it can lead to situations where the node is unable to provide sufficient computing resources and in the worst cases can bring down an entire node. 

From the [Kubernetes Documentation on Resources](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/)

> When you specify a Pod, you can optionally specify how much CPU and memory (RAM) each Container needs. When Containers have resource requests specified, the scheduler can make better decisions about which nodes to place Pods on. And when Containers have their limits specified, contention for resources on a node can be handled in a specified manner.

The main takeaway is that for every container, you have the option to specify a resource `request` and a resource `limit`. The resource limits and requests for a pod is simply the sum of the resource limits and requests for each of the containers in that pod. 

The specifications are defined in the [deployment file](../helm/aladdin-demo/templates/server/deploy.yaml)
```yaml
resources:
  requests:
    cpu: 100m
    memory: 100Mi
  limits:
    cpu: 200m
    memory: 200Mi
```

You can read more about what the cpu and memory units mean [here](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-cpu). 

The `request` above is essentially telling the kubernetes scheduler that this pod needs at least 100 millicores of CPU and 100MiB of memory. The scheduler will look at the requests of all the pods currently scheduled on a node, and will only schedule this pod if the node has at least 100m CPU and 100MiB of memory free. Note that this does not take into account how much resource the pods are actually consuming, only the request it has specified. This tries to ensure that all pods have suficient resources when being scheduled.

The `limit` above puts a cap on the amount of resources the pod can consume. It allows the pod to be throttled if it starts using more than 200m CPU. If the pod uses more than 200MiB of memory, the scheduler will kill the pod and attempt to restart it. This prevents cases where a single pod is hogging all the resources, which could lead to other pods being throttled or evicted.

It is important to note that if a container specifies a resource `limit` but not a resource `request`, then the container's `request` is set to match its `limit`.

This [Medium article](https://medium.com/retailmenot-engineering/what-happens-when-a-kubernetes-pod-uses-too-much-memory-or-too-much-cpu-82165022f489) gives a great walkthrough example of what happens when a kubernetes pod uses too much memory or CPU, and how using resource requests and limits reduce the negative impact.
