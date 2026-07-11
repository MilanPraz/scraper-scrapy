from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select,and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models import Product
from app.schemas import ProductResponse
from app.schemas import ProductCreate
from datetime import datetime ,timezone
from uuid import UUID

from app.utils import to_aware_utc

router = APIRouter(prefix="/products",tags=['products'])




def build_product_search_filter(token:str):

    compact_token= token.lower().replace(" ","")

    return or_(
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
        func.replace(func.lower(Product.variant)," ","").ilike(f"%{compact_token}%")

    )

@router.get("/")
async def get_products(
    session:AsyncSession=Depends(get_async_session),
    q:str | None =None,
    brand: str | None =None,
    category:str | None =None,
    source:str | None = None
    ):
    try:
        # lets create a query SQLAlchemy object to fetch products from the database
        query=select(Product).order_by(Product.created_at.desc())


        if q:
            tokens=[
                token.strip() for token in q.split() if token.strip()
            ]
            query = query.where(
                and_(*[build_product_search_filter(token) for token in tokens])
            )
        # query= query.where(Product.model_name.ilike(f"%{q}%"))

        if brand:
            query=query.where(Product.brand.ilike(f"%{brand}%"))
        
        if category:
            query= query.where(Product.category.ilike(f"%{category}%"))

        if source:
            query= query.where(Product.store.ilike(f"%{source}%"))

        result= await session.execute(query)
        products=result.scalars().all()

        return {
            "message":"Products fetched successfully",
            "count":len(products),
            "data":products
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{product_id}")
async def get_single_product(product_id:UUID,session:AsyncSession = Depends(get_async_session)):

    result = await session.execute(select(Product).where(Product.id==product_id))

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(status_code=404,detail=f"Product with id {product_id} not found")
    
    return {
        "message":"Product fetched successfully",
        "data":{
            "id":str(product.id),
            "store":product.store,
            "category":product.category,
            "brand":product.brand,
            "model_name":product.model_name,
            "variant":product.variant,
            "ram":product.ram,
            "storage":product.storage,
            "price":product.price,
            "price_text":product.price_text,
            "price_type":product.price_type,
            "currency":product.currency,
            "product_url":product.product_url,
            "source_url":product.source_url,
            "in_stock":product.in_stock,
            "scraped_at":product.scraped_at,
            "created_at":product.created_at,
            "updated_at":product.updated_at
    }}

# post method
@router.post("/",response_model=ProductResponse)
async def create_product(payload:ProductCreate,session:AsyncSession=Depends(get_async_session)):
    try:

        data=payload.model_dump()
        data["scraped_at"] = to_aware_utc(data.get("scraped_at"))
    
        product = Product(**data)
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500,detail="Product creation failed: "+str(e))
    

# upsert product

async def upsert_product_data(data:dict,session:AsyncSession):
    try:
        # check if product exists based on store and product_url
        result = await session.execute(
            select(Product).where(Product.store==data["store"],Product.product_url==data['product_url']))
        product= result.scalar_one_or_none()


        if product:
            # update existing product
            for key,value in data.items():
                setattr(product,key,value)

            return product
        product = Product(**data)
        session.add(product)
        return product
    except Exception as e:
        raise HTTPException(status_code=500,detail="Product upsert failed: "+str(e))
        

# what it does
# 1. It checks if a product with the same store and product_url already exists in the database.
# 2. If it exists, it updates the existing product with the new data.

@router.post("/upsert")
async def upsert_product(payload:ProductCreate,session:AsyncSession= Depends(get_async_session)):
    try:
        data= payload.model_dump()
        data["scraped_at"]=to_aware_utc(data.get("scraped_at"))

        product=await upsert_product_data(data,session)

        await session.commit()
        await session.refresh(product)

        return product

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500,detail="Product upsert failed: "+str(e))
       