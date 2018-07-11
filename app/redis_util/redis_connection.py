import redis
import os

redis_conn = None
# TODO: Remove once external (aws) redis script is in place
if os.environ["REDIS_CREATE"] == "true":
    redis_conn = redis.StrictRedis(
        host=os.environ["ALADDIN_DEMO_REDIS_SERVICE_HOST"],
        port=os.environ["ALADDIN_DEMO_REDIS_SERVICE_PORT"],
    )


def ping_redis():
    return redis_conn.ping()
