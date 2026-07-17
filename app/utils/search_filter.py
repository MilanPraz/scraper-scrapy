
from sqlalchemy import func, or_, text

from app.database.models import Product


def build_product_search_filter(token:str):
    compact_token= token.lower().strip().replace(" ","")


    return or_(
        # Normal 
        Product.store.ilike(f"%{token}%"),
        Product.category.ilike(f"%{token}%"),
        Product.brand.ilike(f"%{token}%"),
        Product.model_name.ilike(f"%{token}%"),
        Product.variant.ilike(f"%{token}%"),
        Product.ram.ilike(f"%{token}%"),
        Product.storage.ilike(f"%{token}%"),
        Product.price_text.ilike(f"%{token}%"),

        func.replace(func.lower(Product.ram)," ","").ilike(f"%{compact_token}%"),
        func.replace(func.lower(Product.storage)," ","").ilike(f"%{compact_token}%"),
        func.replace(func.lower(Product.variant)," ","").ilike(f"%{compact_token}%"),

        #fuzzy typo search with pg_trigram
    # Fuzzy typo search using pg_trgm
        func.similarity(
            func.lower(Product.brand),
            token,
        ) > 0.3,

        func.similarity(
            func.lower(Product.model_name),
            token,
        ) > 0.25,

        func.similarity(
            func.lower(Product.category),
            token,
        ) > 0.3,
    )