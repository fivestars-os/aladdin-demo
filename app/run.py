import falcon
import json
from math import sqrt
from redis_util.redis_connection import redis_conn
from elasticsearch_util.elasticsearch_connection import es_conn


class BaseResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = '\n I can show you the world \n \n'


class RedisResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        msg = redis_conn.get('msg')
        resp.body = msg


class BusyResource(object):
    # A computation intense resource to demonstrate autoscaling
    def on_get(self, req, resp):
        n = 0.0001
        for i in range(1000000):
            n += sqrt(n)
        resp.body = 'busy busy...'


class PingResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = ''


class ElasticsearchResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        data = es_conn.get(index='messages', doc_type='song', id=1)
        msg = '\nData from ElasticSearch is {} \n \n'.format(json.dumps(data['_source']))
        resp.body = msg


app = falcon.API()

if redis_conn:
    app.add_route('/app/redis', RedisResource())
if es_conn:
    app.add_route('/app/elasticsearch', ElasticsearchResource())
app.add_route('/app', BaseResource())
app.add_route('/app/busy', BusyResource())
app.add_route('/ping', PingResource())
