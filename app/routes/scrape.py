import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException


router = APIRouter(prefix="/scrape",tags=['scraping'])

# __file__ give the relative path of this current file and resolve makes it absolute like drive d to this file and parents used to move up in dir

SCRAPPER_DIR=Path(__file__).resolve().parents[2] / "scraper"

ALLOWED_SCRAPERS={
    "gadgetbyte",
    "hukut",
    "yantra"
}

def run_spider(spider_name:str,category:str,brand:str):
    # python -m scrapy crawl myspider -a category=electronics -a brand=sony

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

    subprocess.run(command,cwd=SCRAPPER_DIR,check=False)



@router.post('/{spider_name}')
async def trigger_scraper(
    spider_name:str,
    background_tasks:BackgroundTasks,
    category:str ="mobiles",
    brand:str="samsung"
):
    if spider_name not in ALLOWED_SCRAPERS:
        raise HTTPException(status_code=404,detail=f"Scraper {spider_name} not found")
    
    background_tasks.add_task(run_spider,spider_name,category,brand)


    return {
        "message":f" Scraper {spider_name} triggered successfully",
        "category":category,
        "brand":brand,
        "spider_name":spider_name
    }
