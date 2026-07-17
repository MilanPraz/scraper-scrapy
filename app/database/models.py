from sqlalchemy import Column, Float, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped,mapped_column
from app.database.db import Base
from uuid import UUID as PythonUUID, uuid4
from datetime import datetime, timezone

def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def utc_now():
    return datetime.now(timezone.utc)

class Product(Base):

    __tablename__= "products"

    id:Mapped[PythonUUID] = mapped_column(PostgresUUID(as_uuid=True),primary_key=True,default=uuid4)

    # source
    store:Mapped[str]=mapped_column(String(100),nullable=False)
    category:Mapped[str]=mapped_column(String(100),nullable=False)
    brand:Mapped[str]=mapped_column(String(100),nullable=False)

    # product info
    model_name:Mapped[str]=mapped_column(Text,nullable=False)
    variant:Mapped[str | None]=mapped_column(String(100),nullable=True)

    ram:Mapped[str | None]=mapped_column(String(100),nullable=True)
    storage:Mapped[str | None]=mapped_column(String(100),nullable=True)

    # price info
    price:Mapped[float | None]=mapped_column(Float,nullable=True)
    discounted_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_text:Mapped[str | None]=mapped_column(String(100),nullable=True)
    price_type:Mapped[str | None]=mapped_column(String(50),nullable=True)
    currency:Mapped[str]=mapped_column(String(10),nullable=False,default="NPR")

    # urls
    product_url:Mapped[str]=mapped_column(Text,nullable=False)
    source_url:Mapped[str]=mapped_column(Text,nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    #status
    in_stock:Mapped[bool]=mapped_column(nullable=False,default=True)

    #time
    scraped_at:Mapped[DateTime | None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    __table_args__ = (
        UniqueConstraint("store","product_url",name="unique_store_product_url"),
    )
    # same store + same product_url = same product