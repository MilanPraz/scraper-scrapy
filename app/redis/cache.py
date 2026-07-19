import hashlib
import json
from redis.asyncio import Redis
from app.redis.config import CACHE_REDIS_URL, PRODUCT_CACHE_TTL_SECONDS


# let's create an asynchronous connection with Redis
redis_cache= Redis.from_url(
    CACHE_REDIS_URL,
    decode_responses=True
)


def make_products_cache_key(
        q:str | None =None,
        brand: str | None = None,
        category: str | None = None,
        source: str | None =None
)->str:
    params={
        "q":(q or "").strip().lower(),
        "brand":(brand or "").strip().lower(),
        "category":(category or "").strip().lower(),
        "source":(source or "").strip().lower()
    }

    raw_key=json.dumps(params,sort_keys=True)
    hashed_key=hashlib.md5(raw_key.encode()).hexdigest()

    return f"products:list:{hashed_key}"



async def get_cached_products_response(key:str):
    cached_data= await redis_cache.get(key)

    if cached_data is None:
        return None
    
    return json.loads(cached_data)


# this func isi hit when cache miss and we need to set the cache for the products response
async def set_cached_products_response(
        key:str,
        data:dict,
        ttl:int=PRODUCT_CACHE_TTL_SECONDS
):
    await redis_cache.set(
        key,
        json.dumps(data),
        ttl
    )

async def clear_product_cache():
    async for key in redis_cache.scan_iter("products:list:*"):
        await redis_cache.delete(key)


# for suggestions

def make_suggestions_cache_key(q:str|None=None,limit:int=10)->str:
    params={
        "q":(q or "").strip().lower(),
        "limit":limit
    }

    raw_key=json.dumps(params,sort_keys=True)
    hashed_key=hashlib.md5(raw_key.encode()).hexdigest()

    return f"suggestions:list:{hashed_key}"


async def get_cached_suggestions_response(key:str):
    cached_data= await redis_cache.get(key)

    if cached_data is None:
        return None
    
    return json.loads(cached_data)


async def set_cached_suggestions_response(
        key:str,
        data:dict,
        ttl:int=PRODUCT_CACHE_TTL_SECONDS
):
    await redis_cache.setex(
        key,
        ttl,
        json.dumps(data)
    )


async def clear_cache_suggestions():
    async for key in redis_cache.scan_iter("suggestions:list:*"):
        await redis_cache.delete(key)