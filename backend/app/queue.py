import redis
from rq import Queue
from app.config import Config

redis_conn = redis.from_url(Config.REDIS_URL)
queue = Queue('logbeacon', connection=redis_conn)