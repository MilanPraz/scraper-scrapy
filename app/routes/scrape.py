
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.celery.celery_app import celery_app
from app.tasks.scrape_tasks import run_spider_job

router = APIRouter(prefix="/scrape",tags=['scraping'])

# __file__ give the relative path of this current file and resolve makes it absolute like drive d to this file and parents used to move up in dir

SCRAPPER_DIR=Path(__file__).resolve().parents[2] / "scraper"

ALLOWED_SCRAPERS={
    "gadgetbyte",
    "hukut",
    "yantra"
}

# def run_spider(spider_name:str,category:str,brand:str):
#     # python -m scrapy crawl myspider -a category=electronics -a brand=sony

#     command=[
#         sys.executable,
#         "-m",
#         "scrapy",
#         "crawl",
#         spider_name,
#         "-a",
#         f"category={category}",
#         "-a",
#         f"brand={brand}"
#     ]

#     subprocess.run(command,cwd=SCRAPPER_DIR,check=False)





@router.post('/{spider_name}')
async def trigger_scrapper(
    spider_name:str,
    category:str="mobiles",
    brand:str="samsung"
):
    if spider_name not in ALLOWED_SCRAPERS:
        raise HTTPException(status_code=404,detail=f"Scraper {spider_name} not found")
    
    if not SCRAPPER_DIR.exists():
        raise HTTPException(status_code=500,detail=f"Scraper directory {SCRAPPER_DIR} not found")
    
    # Trigger the Celery task to run the spider
    task = run_spider_job.delay(
        spider_name=spider_name,
        category=category,
        brand=brand
    )

    return {
        "message":f" Scraper {spider_name} job Queued!",
        "task_id":task.id,
        "spider_name":spider_name,
        "category":category,
        "brand":brand,
    }


@router.get("/jobs/{task_id}")
async def get_scraper_job_status(task_id:str):
    task_result = celery_app.AsyncResult(task_id)

    response= {
        "task_id":task_id,
        "status":task_result.status,
    }

    if task_result.successful():
        response["result"]=task_result.result

    elif task_result.failed():
        response["error"]=str(task_result.result)

    return response