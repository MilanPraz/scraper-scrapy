import subprocess
import os
import sys
from pathlib import Path
from redis import Redis
from app.celery.celery_app import celery_app
from app.redis.config import REDIS_URL , CACHE_REDIS_URL


SCRAPPER_DIR= Path(__file__).resolve().parents[2] / 'scraper'



def clear_product_cache():
    """
    Clear the product cache in Redis.
    """

    redis_client = Redis.from_url(CACHE_REDIS_URL,decode_responses=True)  # Create a Redis client using the URL from config.py

    for key in redis_client.scan_iter("products:*"):
        redis_client.delete(key)


@celery_app.task(name="scraper.run_spider",bind=True)
def run_spider_job(self,spider_name:str,category:str="mobiles",brand:str="samsung"):
    
    command=[
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        spider_name,
        "-a",
        f"category={category}",
        "-a",
        f"brand={brand}"
    ]

    result=subprocess.run(
        command,
        cwd=SCRAPPER_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Log the error message
        error_message = result.stderr[-4000:]
        raise Exception(f"Scrapy spider failed with error: {error_message}")
    
    # Clear product API cache after fresh scraped data is saved
    clear_product_cache()  

    return {
        "message":f"Scraper {spider_name} triggered successfully",
        "spider_name":spider_name,
        "category":category,
        "brand":brand,
        "returncode":result.returncode,
        "stdout":result.stdout[-2000:],
        "stderr":result.stderr[-2000:]
    }