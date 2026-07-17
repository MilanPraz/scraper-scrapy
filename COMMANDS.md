## For Migration - Alembic

```code
uv run alembic init -t async alembic
```

This creates:

```code
alembic/
├── env.py
├── versions/
alembic.ini
```

Alembic can autogenerate candidate migration files by comparing your current database schema with your SQLAlchemy model metadata, but the docs also say you should review generated migrations manually.

To run the application

````code
uvicorn app.main:app --reload



```code
uv run alembic revision --autogenerate -m "make product timestamps timezone aware"
````

## Production Level Phase

Install Packages

```
uv add celery redis python-dotenv
```

### Since we have made this docker-compose.yml file

we are here tryiing to run redis through docker

1st we neeed to compose up

```
docker compose up -d redis
```

To run Celery Worker

```
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

Fix 5: Clear old broken queued tasks

Because Redis may still contain old task messages, purge them:

```
celery -A app.celery_app.celery_app purge
```

PENDING
STARTED
SUCCESS
FAILURE

# Migration Steps

run this cmd:

```
uv run alembic revision --autogenerate -m "add image url and discounted price to products"
```

then apply migration:

```
uv run alembic upgrade head
```
