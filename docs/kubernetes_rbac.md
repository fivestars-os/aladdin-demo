# Kubernetes RBAC

In Kubernetes version 1.8, they added stable support for role based access control (RBAC). This is to use best security practices when your processes in your pods need to perform requests against the kubernetes apiserver (via kubectl, code libraries, etc) by locking down _exactly_ which resources it can access and how it can access them. The kubernetes documentation can be found [here]( https://kubernetes.io/docs/reference/access-authn-authz/rbac/). Note for the following examples to work, your kubernetes apiserver must have the `--authorization-mode=RBAC` flag enabled. On recent versions of minikube, this is the default.

# Roles and ClusterRoles
In kubernetes RBAC, we have roles and clusterroles. Roles are namespace scoped, and can only allow permissions to things within the namespace. Clusterroles are cluster scoped and can allow permissions to resources in other namespaces, or resources that aren't namespace scoped, e.g. nodes.

In our example, we will have a command in our commands pod that needs to list all the pods for aladdin-demo
```python
import os

from kubernetes import client, config

def parse_args(sub_parser):
    subparser = sub_parser.add_parser("get-pods", help="Get all aladdin-demo pods")
    subparser.set_defaults(func=get_pods)


def get_pods(arg):
    print(get_aladdin_demo_pods())

def get_aladdin_demo_pods():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    res = v1.list_namespaced_pod(
        namespace=os.environ["NAMESPACE"],
        label_selector="project=aladdin-demo")
    return [r.metadata.name for r in res.items]
```
This uses the python kubernetes library to query the kubernetes api server to get all the aladdin demo pods.

You can try this out by starting aladdin demo: `aladdin start` and then running `aladdin cmd aladdin-demo get-pods`.
This works because we have created the necessary RBAC kubernetes resources which permit the commands pod to make such queries against the kubernetes apiserver.

To see what happens without the RBAC resources, first start aladdin-demo with rbac disabled: `aladdin start --set-override-values rbac.enabled=false`. Then run the same command again: `aladdin cmd aladdin-demo get-pods`. This time you should see some 401 unauthorized error.

So how does this work? Let's take a look at our rbac file:
```yaml
{{ if .Values.rbac.enabled }}
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ .Chart.Name }}-commands
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-commands
    app: {{ .Chart.Name }}-commands
    githash: {{ .Values.deploy.imageTag | quote }}
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ .Chart.Name }}-commands
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-commands
    app: {{ .Chart.Name }}-commands
    githash: {{ .Values.deploy.imageTag | quote }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ .Chart.Name }}-commands
subjects:
- kind: ServiceAccount
  name: {{ .Chart.Name }}-commands
  namespace: {{ .Release.Namespace }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Chart.Name }}-commands
  labels:
    project: {{ .Chart.Name }}
    name: {{ .Chart.Name }}-commands
    app: {{ .Chart.Name }}-commands
    githash: {{ .Values.deploy.imageTag | quote }}
{{ end }}
```

Here we create 3 kubernetes resources: a Role, a RoleBinding, and a ServiceAccount.

The role specifies which permissions we want to allow. Here we allow "get" and "list" on the pods resource.

The RoleBinding allows us to bind the role to some set of subjects. Here, the subject is a serviceAccount, which is the third resource we create.

Then, we reference this serviceAccount in our commands deploy yaml:
```yaml
{{ if .Values.rbac.enabled }}
      serviceAccountName: {{ .Chart.Name }}-commands
{{ end }}
```
That's all there is to it.
