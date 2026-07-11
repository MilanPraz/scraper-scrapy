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
