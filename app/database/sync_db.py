from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SYNC= os.getenv("DATABASE_URL_SYNC","")

# scrappy is mostly synchronous, use a synchronous engine and session for scrappy to use

if not DATABASE_URL_SYNC:
    raise RuntimeError("DATABASE_URL_SYNC is missing in .env")


sync_engine=create_engine(DATABASE_URL_SYNC,echo=True)

SyncSessionLocal=sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)