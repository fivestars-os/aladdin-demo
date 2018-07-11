import requests
import os

from redis.exceptions import RedisError
from redis_util.redis_connection import ping_redis
from elasticsearch import ElasticsearchException
from elasticsearch_util.elasticsearch_connection import get_es_health


def parse_args(sub_parser):
    subparser = sub_parser.add_parser("status", help="Report on the status of the application")
    # register the function to be executed when command "status" is called
    subparser.set_defaults(func=print_status)


def print_status(arg):
    """ Prints the status of the aladdin-demo pod and the redis pod """
    print_aladdin_demo_server_status()
    print_redis_status()
    print_elasticsearch_status()


def print_aladdin_demo_server_status():
    print("pinging aladdin-demo-server ...")
    host = os.environ["ALADDIN_DEMO_SERVER_SERVICE_HOST"]
    port = os.environ["ALADDIN_DEMO_SERVER_SERVICE_PORT"]
    url = "http://{}:{}/ping".format(host, port)
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print("aladdin demo server endpoint ping successful")
        else:
            print("aladdin demo server endpoint ping returned with status code {}".format(r.status_code))
    except requests.exceptions.ConnectionError as e:
        print("aladdin demo endpoint connection error: {}".format(e))


def print_redis_status():
    # TODO have this ping external redis when that gets added
    print("pinging redis ...")
    if os.environ["REDIS_CREATE"] == "false":
        print("redis creation flag set to false, no other redis connection available at this time")
        return
    try:
        status = ping_redis()
        print("redis connection ping successful {}".format(status))
    except RedisError as e:
        print("redis connection error: {}".format(e))


def print_elasticsearch_status():
    print("getting elasticsearch health ...")
    if os.environ["ELASTICSEARCH_CREATE"] == "false":
        print("elasticsearch creation flag set to false, no other elasticsearch connection available at this time")
        return
    try:
        status = get_es_health()
        print("elasticsearch health retrieved: {}".format(status))
    except ElasticsearchException as e:
        print("encountered elasticsearch error: {}".format(e))
