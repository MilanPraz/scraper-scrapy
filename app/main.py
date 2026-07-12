from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import create_db_and_tables, get_async_session
from app.routes import products
from app.routes import scrape


@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield 


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include the routers for products
app.include_router(products.router,prefix="/api")
app.include_router(scrape.router,prefix="/api/scrape")

@app.get("/")
def root():
    return {
        "message":"Hello World!"
    }