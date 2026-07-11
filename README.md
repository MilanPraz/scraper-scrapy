# Price Comparison API

A FastAPI + Scrapy based price comparison backend for scraping product prices from Nepali ecommerce and tech websites, normalizing product data, storing the latest useful data in PostgreSQL, and serving searchable product APIs.

## Current Version

`v0.0.1` - Initial Product Scraping API Foundation

## Project Status

This project currently supports:

- FastAPI backend setup
- PostgreSQL/Aiven database connection
- SQLAlchemy Product model
- Pydantic request and response schemas
- Product create API
- Product list/search API
- Single product detail API
- Product upsert logic using `store + product_url`
- Scrapy project integrated into the backend project
- Scrapy pipeline connected to PostgreSQL
- Scraped product data normalized and saved into the database

## Current Architecture

```txt
Scrapy Spider
    ↓
Scrapy Item
    ↓
Scrapy Pipeline
    ↓
Normalize / Clean Product Data
    ↓
Upsert into PostgreSQL
    ↓
FastAPI Product API
    ↓
Search / Filter Products
```

Current working flow:

```txt
Manual Scrapy Command
        ↓
Scrapy runs spider
        ↓
Spider yields product item
        ↓
Pipeline receives item
        ↓
Pipeline checks store + product_url
        ↓
If product exists: update product
If new product: insert product
        ↓
PostgreSQL stores latest product data
        ↓
FastAPI serves products through API
```

Planned production architecture:

```txt
FastAPI
  ↓
Redis Queue / Celery / RQ
  ↓
Scrapy Worker
  ↓
PostgreSQL
  ↓
Redis Cache
  ↓
FastAPI Product API
```

## Tech Stack

- **FastAPI** - API backend
- **Scrapy** - Web scraping framework
- **PostgreSQL / Aiven** - Product data storage
- **SQLAlchemy** - ORM and database queries
- **Pydantic** - Request/response validation
- **Alembic** - Database migrations
- **uv** - Python package and environment management
- **psycopg** - Sync PostgreSQL driver for Scrapy pipeline
- **asyncpg** - Async PostgreSQL driver for FastAPI

## Folder Structure

```txt
TEST/
├── app/
│   ├── main.py
│   ├── db.py              # Async database connection for FastAPI
│   ├── sync_db.py         # Sync database connection for Scrapy pipeline
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── utils.py           # Shared helper functions
│   └── routes/
│       ├── products.py    # Product APIs
│       └── scrape.py      # Future scrape trigger API
│
├── scraper/
│   ├── scrapy.cfg
│   └── price_comparison_nepal/
│       ├── spiders/
│       │   ├── gadgetbyte.py
│       │   ├── hukut.py
│       │   └── yantra.py
│       ├── items.py
│       ├── pipelines.py   # Saves/upserts scraped products into PostgreSQL
│       ├── settings.py
│       ├── sources.py
│       └── utils.py
│
├── alembic/
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

## Product Data Model

The product model is designed to match the Scrapy item fields.

Main fields:

```txt
store
category
brand
model_name
variant
ram
storage
price
price_text
price_type
currency
product_url
source_url
in_stock
scraped_at
created_at
updated_at
```

The database uses this unique rule:

```python
UniqueConstraint("store", "product_url", name="unique_store_product_url")
```

This means the same store cannot save the same product URL twice. If Scrapy finds the same product again, the existing row should be updated instead of creating duplicate rows.

## Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql+asyncpg://username:password@host:port/dbname?ssl=require
DATABASE_URL_SYNC=postgresql+psycopg://username:password@host:port/dbname?sslmode=require
```

Important:

- `DATABASE_URL` is used by FastAPI async database sessions.
- `DATABASE_URL_SYNC` is used by Scrapy pipeline sync database sessions.
- Do not commit `.env` to GitHub.
- Use `.env.example` for sharing sample variables.

## Installation

Clone the repository:

```bash
git clone https://github.com/MilanPraz/scraper-scrapy.git
cd scraper-scrapy
```

Create and activate virtual environment using uv:

```bash
uv venv
```

On Windows PowerShell:

```bash
.venv\Scripts\activate
```

On Git Bash / Linux / macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
uv sync
```

If needed, install manually:

```bash
uv add fastapi uvicorn sqlalchemy asyncpg psycopg[binary] pydantic python-dotenv alembic scrapy
```

## Running FastAPI

From the project root:

```bash
uv run uvicorn app.main:app --reload
```

Open Swagger docs:

```txt
http://127.0.0.1:8000/docs
```

## Running Scrapy Manually

Go to the scraper folder:

```bash
cd scraper
```

Run a spider:

```bash
uv run scrapy crawl gadgetbyte
```

Example with spider arguments:

```bash
uv run scrapy crawl gadgetbyte -a category=mobiles -a brand=samsung
```

After scraping, check the products from FastAPI:

```txt
GET /products/
GET /products/?q=samsung
GET /products/?q=redmi 4gb
```

## API Endpoints

### Root

```txt
GET /
```

Returns basic API status.

### List Products

```txt
GET /products/
```

Optional query parameters:

```txt
q
brand
category
source
```

Examples:

```txt
GET /products/?q=samsung f22 6gb
GET /products/?brand=samsung
GET /products/?category=mobiles
GET /products/?source=GadgetByte Nepal
```

### Get Single Product

```txt
GET /products/{product_id}
```

Returns a single product by UUID.

### Create Product

```txt
POST /products/
```

Sample body:

```json
{
  "store": "GadgetByte Nepal",
  "category": "Mobiles",
  "brand": "Samsung",
  "model_name": "Samsung Galaxy F22",
  "variant": "6GB/128GB",
  "ram": "6GB",
  "storage": "128GB",
  "price": 15000,
  "price_text": "Rs. 15,000",
  "price_type": "exact",
  "currency": "NPR",
  "product_url": "https://example.com/samsung-f22",
  "source_url": "https://example.com/mobile-price-list",
  "in_stock": true
}
```

### Upsert Product

```txt
POST /products/upsert
```

If a product with the same `store + product_url` exists, it updates the product. Otherwise, it creates a new product.

## Search Logic

The product search supports combined search terms.

Example:

```txt
GET /products/?q=samsung f22 6gb
```

The query is split into tokens:

```txt
samsung
f22
6gb
```

Each token is searched across multiple fields:

```txt
store
category
brand
model_name
variant
ram
storage
price_text
```

The logic is:

```txt
samsung must match somewhere
AND
f22 must match somewhere
AND
6gb must match somewhere
```

This allows flexible product search by brand, model, RAM, storage, or variant.

## Database Migrations

Alembic is used for database migrations.

Generate a migration:

```bash
uv run alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Important:

- `create_all()` only creates missing tables.
- It does not update existing columns.
- Use Alembic for real schema changes.

## Scrapy Pipeline Behavior

The Scrapy pipeline receives each scraped product item and performs this flow:

```txt
Receive item
    ↓
Convert item to dict
    ↓
Normalize scraped_at datetime
    ↓
Check existing product by store + product_url
    ↓
If exists: update product fields
If new: create product
    ↓
Commit to PostgreSQL
```

This keeps the database clean by saving only the latest useful product data.

## Current Limitations

- Scrapy is currently run manually from the terminal.
- FastAPI scrape trigger endpoint is planned but not finalized.
- No scrape job tracking yet.
- No Redis cache yet.
- No Celery/RQ background job system yet.
- No frontend/admin dashboard yet.

## Roadmap

Planned next steps:

- Add `POST /scrape/{spider_name}` endpoint to trigger spiders from FastAPI
- Add scrape job tracking table
- Add scrape job status APIs
- Add Redis cache for product search results
- Replace simple background execution with Celery/RQ + Redis
- Add price history table
- Add frontend/admin dashboard
- Add deployment setup

## Security Notes

Never commit real database credentials.

Make sure these files are ignored:

```gitignore
.env
.venv/
__pycache__/
.scrapy/
```

If a real database password was committed or shared, rotate/regenerate it immediately from the database provider dashboard.

## Version

Current release:

```txt
v0.0.1
```

This version focuses on the first working backend foundation for scraping, saving, and serving product price data.
