from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime,timezone
from sqlalchemy import select
import sys
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
    
from app.database.models import Product
from app.database.sync_db import SyncSessionLocal


def utc_now():
    return datetime.now(timezone.utc)

def to_aware_utc(value):
    if value is None:
        return utc_now()
    if isinstance(value,datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        else:
            return value.astimezone(timezone.utc)
    return utc_now()

class ProductValidationPipeline:
    """
    Validate common product fields and exact-variant
    fields separately.
    """

    common_required_fields = (
        "store",
        "category",
        "brand",
        "model_name",
        "price",
        "price_type",
        "currency",
        "product_url",
        "source_url",
        "scraped_at",
    
    )

    exact_price_required_fields = (
        # "variant",
        "storage",

    )

    def process_item(self, item):
        adapter = ItemAdapter(item)

        for field_name in self.common_required_fields:
            value = adapter.get(field_name)

            if value is None or value == "":
                raise DropItem(
                    f"Missing required field: "
                    f"{field_name}"
                )

        price = adapter.get("price")

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
        ):
            raise DropItem(
                f"Invalid price type for "
                f"{adapter.get('model_name')}: "
                f"{price}"
            )

        if price <= 0:
            raise DropItem(
                f"Invalid price for "
                f"{adapter.get('model_name')}: "
                f"{price}"
            )

        price_type = adapter.get("price_type")

        if price_type not in {
            "exact",
            "starting",
        }:
            raise DropItem(
                f"Invalid price type: {price_type}"
            )

        # GadgetByte and other exact prices must
        # contain variant information.
        if price_type == "exact":
            for field_name in (
                self.exact_price_required_fields
            ):
                value = adapter.get(field_name)

                if value is None or value == "":
                    raise DropItem(
                        f"Exact offer is missing "
                        f"{field_name}: "
                        f"{adapter.get('model_name')}"
                    )

        return item


class DuplicateProductRemovePipeline:
    def __init__(self):
        self.seen_offers: set[tuple[str, ...]] = set()

    def process_item(self, item):
        adapter = ItemAdapter(item)

        unique_key = (
            str(adapter.get("store", ""))
            .strip()
            .lower(),
            str(adapter.get("category", ""))
            .strip()
            .lower(),
            str(adapter.get("brand", ""))
            .strip()
            .lower(),
            str(adapter.get("model_name", ""))
            .strip()
            .lower(),
            str(adapter.get("variant") or "")
            .strip()
            .lower(),
            str(adapter.get("price_type", ""))
            .strip()
            .lower(),
            str(adapter.get("product_url", ""))
            .strip()
            .lower(),
        )

        if unique_key in self.seen_offers:
            raise DropItem(
                f"Duplicate product: "
                f"{adapter.get('store')} "
                f"{adapter.get('model_name')}"
            )

        self.seen_offers.add(unique_key)

        return item
    

class SaveProductToDatabasePipeline:

    def process_item(self,item):
        session= SyncSessionLocal()

        try:
            data= dict(item)

            data["scraped_at"]=to_aware_utc(data.get("scraped_at"))

            # Important: DB does not allow NULL for in_stock
            if data.get("in_stock") is None:
                data["in_stock"] = True


            result=session.execute(
                select(Product).where(
                    Product.store==data["store"],
                    Product.product_url==data['product_url']
                )
            )

            product= result.scalar_one_or_none()

            if product:
                for key,value in data.items():
                    setattr(product,key,value)
                product.updated_at=utc_now()
            else:
                product=Product(**data)
                session.add(product)

            session.commit()
            return item
        except Exception as e:
            session.rollback()
            raise DropItem(
                f"Database error: {str(e)}"
            )
        finally:
            session.close()