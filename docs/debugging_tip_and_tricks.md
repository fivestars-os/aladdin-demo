# Debugging Tips and Tricks

Here are some useful tips and tricks to help you debug your application.

## Shell into a Kubernetes Container
Often times when things are behaving strangly, it may be very beneficial to shell into the container to poke around, check that the expected volumes have all been mounted in the correct places, or run some commands directly. Aladdin has a command to help with this. 

### Aladdin Connect
Connect is one of aladdin's commands used to connect to a container's shell. This command finds the pods related to a supplied deployment name. If only one pod with a single container is found, it connects directly to that container's shell. We first try `bash`, but if that doesn't work, we settle on `sh`. If multiple pods-container pairs are found that contain the supplied deployment name, they are all listed, and an index must be chosen. 
```
usage: aladdin connect [-h] [--namespace NAMESPACE] [app]

positional arguments:
  app                   which app to connect to

optional arguments:
  -h, --help            show this help message and exit
  --namespace NAMESPACE, -n NAMESPACE
                        namespace name, defaults to default current :
                        [default]
```
Example:
```
  > aladdin connect aladdin-demo-server

Available:
----------
0: pod aladdin-demo-server-786c967bff-xlfrs; container aladdin-demo-nginx
1: pod aladdin-demo-server-786c967bff-xlfrs; container aladdin-demo-uwsgi
2: pod aladdin-demo-server-f66fb6c5d-754pv; container aladdin-demo-nginx
3: pod aladdin-demo-server-f66fb6c5d-754pv; container aladdin-demo-uwsgi
Choose an index:
```
One thing to keep in mind is that this only works for running containers. So if your container has encountered an error and is not currently running, you will not be able to access it. One workaround to this is to replace you ENTRYPOINT with a `sleep infinity` command of some sort. This way, the container will start but then immediately go to sleep indefinitely and will not encounter an error. You can then shell into the container and manually run your code to examine any errors that may occur.
