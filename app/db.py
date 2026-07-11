from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship


DATABASE_URL= "postgresql+asyncpg://avnadmin:AVNS_yp0t9X_pVKKoGpSjZEQ@pg-3121b00b-scrape.c.aivencloud.com:11782/defaultdb?ssl=require"

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL,echo=True)
async_session_maker= async_sessionmaker(engine,expire_on_commit=False)

async def get_async_session()->AsyncGenerator[AsyncSession,None]:
    async with async_session_maker() as session:
        yield session

        # Here is the session for this request.
        # After the request is done, come back here and clean it up.


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
