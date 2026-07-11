from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class ProductCreate(BaseModel):
    store: str
    category: str
    brand: str

    model_name: str
    variant: str | None = None

    ram: str | None = None
    storage: str | None = None

    price: float | None = None
    price_text: str | None = None
    price_type: str | None = None
    currency: str = "NPR"

    product_url: str
    source_url: str

    in_stock: bool = True
    scraped_at: datetime | None = None

class ProductResponse(ProductCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)