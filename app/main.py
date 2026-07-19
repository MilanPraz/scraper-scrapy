from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import create_db_and_tables, get_async_session
from app.routes import products
from app.routes import scrape
from app.routes import suggestions

# slowapi
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
# from slowapi import _rate_limit_exceeded_handler
from app.limiter.rate_limiter import limiter ,rate_limit_exceeded_handler



@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield 


app = FastAPI(lifespan=lifespan)

app.state.limiter=limiter


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'https://kati-ho.vercel.app',
        'https://katiho.milanprajapati.com.np'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SlowAPIMiddleware
)
# include the routers for products
app.include_router(products.router,prefix="/api")
app.include_router(suggestions.router,prefix="/api")
app.include_router(scrape.router,prefix="/api/scrape")

@app.get("/")
def root():
    return {
        "message":"Hello World!"
    }