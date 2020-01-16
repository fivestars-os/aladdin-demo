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
        label_selector=f"project={os.environ['PROJECT_NAME']}")
    return [r.metadata.name for r in res.items]
