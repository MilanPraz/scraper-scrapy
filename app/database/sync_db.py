from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL= os.getenv("DATABASE_URL_SYNC","")

# scrappy is mostly synchronous, use a synchronous engine and session for scrappy to use

sync_engine=create_engine(DATABASE_URL,echo=True)

SyncSessionLocal=sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)