import os
from elasticsearch import Elasticsearch

es_conn = None
# TODO: Remove once external (aws) script is in place
if os.environ["ELASTICSEARCH_CREATE"] == "true":
    es_conn = Elasticsearch(hosts=os.environ["ELASTICSEARCH_HOST"])


def get_es_health():
    return es_conn.cluster.health()
