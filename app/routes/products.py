from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select,and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.limiter.rate_limiter import limiter
from app.database.db import get_async_session
from app.database.models import Product
from app.schemas.schemas import ProductResponse
from app.schemas.schemas import ProductCreate
from app.utils.search_filter import build_product_search_filter
from uuid import UUID

# from app.utils import to_aware_utc

from app.redis.cache import (
    make_products_cache_key,
    clear_product_cache,
    set_cached_products_response,
    get_cached_products_response 
)
from scraper.price_comparison_nepal.pipelines import to_aware_utc

router = APIRouter(prefix="/products",tags=['products'])




# def build_product_search_filter(token:str):

#     compact_token= token.lower().replace(" ","")

#     return or_(
#         Product.store.ilike(f"%{token}%"),
#         Product.category.ilike(f"%{token}%"),
#         Product.brand.ilike(f"%{token}%"),
#         Product.model_name.ilike(f"%{token}%"),
#         Product.variant.ilike(f"%{token}%"),
#         Product.ram.ilike(f"%{token}%"),
#         Product.storage.ilike(f"%{token}%"),
#         Product.price_text.ilike(f"%{token}%"),

#         func.replace(func.lower(Product.ram)," ","").ilike(f"%{compact_token}%"),
#         func.replace(func.lower(Product.storage)," ","").ilike(f"%{compact_token}%"),
#         func.replace(func.lower(Product.variant)," ","").ilike(f"%{compact_token}%")

#     )

@router.get("/")
@limiter.limit("30/minute")
async def get_products(
    request:Request,
    session:AsyncSession=Depends(get_async_session),
    q:str | None =None,
    brand: str | None =None,
    category:str | None =None,
    source:str | None = None
    ):
    try:
        #redis cache implement

        cache_key= make_products_cache_key(q,brand,category,source)

        cached_response=await get_cached_products_response(cache_key)

        if cached_response:
            cached_response["cached"]=True
            return cached_response


        # lets create a query SQLAlchemy object to fetch products from the database
        query=select(Product)


        if q:
            tokens=[
                token.strip() for token in q.split() if token.strip()
            ]
            for token in tokens:
                query = query.where(build_product_search_filter(token))
        # query= query.where(Product.model_name.ilike(f"%{q}%"))

        if brand:
            query=query.where(Product.brand.ilike(f"%{brand}%"))
        
        if category:
            query= query.where(Product.category.ilike(f"%{category}%"))

        if source:
            query= query.where(Product.store.ilike(f"%{source}%"))

        if q:
            q_lower=q.lower()

            query = query.order_by(
                func.greatest(
                    func.similarity(func.lower(Product.brand),q_lower),
                    func.similarity(func.lower(Product.model_name),q_lower),
                    func.similarity(func.lower(Product.category),q_lower),
                ).desc()
                ,Product.created_at.desc() 
            )
        else:
            query = query.order_by(Product.created_at.desc())
            

        result= await session.execute(query)
        products=result.scalars().all()

        products_data=[
            ProductResponse.model_validate(product).model_dump(mode="json") for product in products
        ]

        response = {
            "message":"Products fetched successfully",
            "count":len(products),
            "data":products_data,
            "cached":False
        }

        # cache the response in redis for future requests
        await set_cached_products_response(cache_key,response)

        return response
    
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

        # await clear_product_cache()

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

# this is not for scraper , just for swagger test
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
       

