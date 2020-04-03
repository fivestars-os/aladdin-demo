import redis
import os

redis_conn = None
# TODO: Remove once external (aws) redis script is in place
if os.environ["REDIS_CREATE"] == "true":
    redis_conn = redis.StrictRedis(
        # These environment variables are provided by kubernetes's service discovery functionality,
        # and derived from the deployment name (which by convention in this case is <project>-redis)
        host=os.environ["REDIS_SERVICE_HOST"],
        port=os.environ["REDIS_SERVICE_PORT"],
    )


def ping_redis():
    return redis_conn.ping()
