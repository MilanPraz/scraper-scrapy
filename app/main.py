from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database.db import create_db_and_tables, get_async_session
from app.routes import products
from app.routes import scrape


@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield 


app = FastAPI(lifespan=lifespan)

# include the routers for products
app.include_router(products.router,prefix="/api")
app.include_router(scrape.router,prefix="/api/scrape")

@app.get("/")
def root():
    return {
        "message":"Hello World!"
    }