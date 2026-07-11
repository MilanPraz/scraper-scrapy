from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL= "postgresql+psycopg://avnadmin:AVNS_yp0t9X_pVKKoGpSjZEQ@pg-3121b00b-scrape.c.aivencloud.com:11782/defaultdb?sslmode=require"

# scrappy is mostly synchronous, use a synchronous engine and session for scrappy to use

sync_engine=create_engine(DATABASE_URL,echo=True)

SyncSessionLocal=sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)