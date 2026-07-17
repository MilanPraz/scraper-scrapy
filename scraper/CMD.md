# Scrapy needs to be run from the folder where scrapy.cfg exists.

structure is:

test/
├── app/
├── scraper/
│ ├── scrapy.cfg
│ └── price_comparison_nepal/

So run this:

```
cd D:/python/fastapi/test/scraper
uv run scrapy crawl hukut -a category=mobiles -a brand=all -O outputs/hukut/hukut_test.csv
```
