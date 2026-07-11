# Current working architecture

```
User / Swagger / Frontend

↓

FastAPI

↓

Product APIs

↓

PostgreSQL
```

## What is already completed

### completed these parts:

```
✅ FastAPI project setup
✅ PostgreSQL/Aiven database connected
✅ SQLAlchemy Product model created
✅ ProductCreate and ProductResponse schemas created
✅ POST /products/ tested
✅ GET /products/ with search/filter created
✅ GET /products/{product_id} created
✅ Upsert logic created
✅ Scrapy project moved inside FastAPI project
✅ Scrapy pipeline connected to same PostgreSQL database
✅ Scrapy successfully scraped and saved products into DB
```

### So the current actual flow is:

```
Manual Scrapy Command
        ↓
Scrapy runs spider: gadgetbyte / hukut / yantra
        ↓
Spider yields product item
        ↓
Pipeline receives item
        ↓
Pipeline converts scraped_at, fixes data
        ↓
Pipeline checks store + product_url
        ↓
If product exists: update
If new product: insert
        ↓
PostgreSQL stores latest product data
        ↓
FastAPI GET /products serves that saved data
```

### Your current folder architecture

Something like this:

```
TEST/
├── app/
│   ├── main.py
│   ├── db.py              # async DB for FastAPI
│   ├── sync_db.py         # sync DB for Scrapy pipeline
│   ├── models.py          # Product model
│   ├── schemas.py         # ProductCreate/ProductResponse
│   ├── utils.py           # datetime helpers
│   └── routes/
│       ├── products.py    # product API
│       └── scrape.py      # next: trigger spider from API
│
├── scraper/
│   ├── scrapy.cfg
│   └── price_comparison_nepal/
│       ├── spiders/
│       │   ├── gadgetbyte.py
│       │   ├── hukut.py
│       │   └── yantra.py
│       ├── items.py
│       ├── pipelines.py   # saves/upserts to DB
│       ├── settings.py
│       └── utils.py
│
├── alembic/
├── pyproject.toml
└── uv.lock
```
