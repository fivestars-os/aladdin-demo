from redis_connection import redis_conn

if __name__ == "__main__":
    redis_conn.set('msg', '\n I can show you the world from Redis\n \n')
