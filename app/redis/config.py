import os
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0") # here /0 means the db number, redis has 16 dbs by default, we are using 0th db for caching and 1st db for celery result backend

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL) # Celery needs a 'message broker' to pass messages between the main application and the worker processes. Redis is a popular choice for this purpose. The broker URL specifies the location of the Redis server that Celery will use to send and receive messages.

CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND","redis://localhost:6379/1") # Once worker finishes the task . where should the result be saved? This is where the result backend comes into play. In this case, we are using Redis again, but this time we are using the 1st db of Redis to store the results of the tasks executed by Celery workers.

PRODUCT_CACHE_TTL_SECONDS = int(os.getenv("PRODUCT_CACHE_TTL_SECONDS","300")) # it is the time to live for the cache in seconds. After this time, the cached data will be considered stale and will be removed from the cache. The default value is 300 seconds (5 minutes).

CACHE_REDIS_URL=os.getenv("CACHE_REDIS_URL",REDIS_URL) # This is the URL for the Redis server that will be used for caching. If not specified, it defaults to the same Redis server used for the Celery broker.

PRODUCT_CACHE_TTL_SECONDS= int(os.getenv("PRODUCT_CACHE_TTL_SECONDS","300")) # it is the time to live for the cache in seconds. After this time, the cached data will be considered stale and will be removed from the cache. The default value is 300 seconds (5 minutes).