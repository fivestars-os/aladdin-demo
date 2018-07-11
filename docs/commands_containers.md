# Commands Containers

Aladdin allows project-specific commands to be managed and implemented within the project repository. These commands can be run independently/directly, or from within aladdin through `aladdin cmd <project name> <command name>`. To do this, we will spin up a dedicated commands pod that is specific to each project. 

In this template project, we demonstrate a simple `status` command, which will ping the relevant endpoints for aladdin-demo and print out each of their statuses. Running `kubectl get pods` should show that `aladdin-demo-commands-<hash>` is running alongside the other `aladdin-demo` pods. The status command can be run using aladdin with:
    
    $ aladdin cmd aladdin-demo status

## Define Command Functions
We start off by creating a [commands_app](../app/commands_app) folder that contains the [requirements](../app/commands_app/requirements.txt) for the commands that need to be run, and a [commands](../app/commands_app/commands) folder that has separate files for each command. In this case, we want to run `status`, so we create [status.py](../app/commands_app/commands/status.py). 

The only required function in [status.py](../app/commands_app/commands/status.py) is a `parse_args(sub_parser)` function. Aladdin will look for this function when you try to run your command. The command `status` must be added to the `sub_parser`, and `set_defaults` should take a function that points to the function that actually runs.
```python
def parse_args(sub_parser):
    subparser = sub_parser.add_parser("status", help="Report on the status of the application")
    # register the function to be executed when command "status" is called
    subparser.set_defaults(func=print_status)
    
def print_status(arg):
    ...
```
## Create Docker Container

We will also need to create a Dockerfile for this container. The image for this commands container must be inherited from the aladdin `commands_base` docker image, and copy over the folder containing the command functions as `command`. We demonstrate this in the [Dockerfile](../app/commands_app/Dockerfile). 
```Dockerfile
FROM fivestarsos/commands-base:1.0.0
...
COPY commands_app/commands commands
```
Update the [build docker script](../build/build_docker.sh) to build the commands container as well.

```shell
docker_build "aladdin-demo-commands" "app/commands_app/Dockerfile" "app"
```
## Create Kubernetes Deploy File
We create [commands/deploy.yaml](../helm/aladdin-demo/templates/commands/deploy.yaml).

## Update lamp.json
Include the commands container image in `docker_images`.
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
