# product suggestion
from fastapi import APIRouter,Depends,HTTPException,Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_async_session
from sqlalchemy import select,func,or_,and_
from app.database.models import Product
from app.redis.cache import (
    make_suggestions_cache_key,
    get_cached_suggestions_response,
    set_cached_suggestions_response
)
from app.limiter.rate_limiter import limiter
router= APIRouter(prefix="/suggestions",tags=["suggestions"])


@router.get("/")
@limiter.limit("60/minute")
async def get_suggestions(
    request: Request,
    q:str= Query(...,min_length=1),
    limit:int= Query(default=10, ge=1, le=100),
    session:AsyncSession=Depends(get_async_session)
):
    try:
        q_clean= q.strip().lower()

        # check redis 1st
        cache_key = make_suggestions_cache_key(q_clean,limit)
        cached_response = await get_cached_suggestions_response(cache_key)

        if cached_response:
            cached_response["cached"]=True
            cached_response["source"] = "redis"

            return cached_response
        
        query = (
            select(Product)
            .where(
                or_(
                    Product.model_name.ilike(f"%{q_clean}%"),
                    Product.brand.ilike(f"%{q_clean}%"),
                    func.similarity(
                        func.lower(Product.model_name),
                        q_clean
                    )>0.25,
                    func.similarity(
                        func.lower(Product.brand),
                        q_clean
                    )>0.3
                )
            ).order_by(
                func.greatest(
                    func.similarity(
                        func.lower(Product.model_name),
                        q_clean
                    ),
                    func.similarity(
                        func.lower(Product.brand),
                        q_clean
                    )
                ).desc(),
                Product.created_at.desc()
            ).limit(limit)
        )

        result = await session.execute(query)
        products=result.scalars().all()

        data=[
            {
               "label": product.model_name,
                "value": product.model_name,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "price": product.price,
                "price_text": product.price_text,
                "store": product.store,
            }
            for product in products
        ]
        response= {
            "query": q,
            "limit": limit,
            "cached": False,
            "count": len(data),
            "data": data,
        }
        await set_cached_suggestions_response(cache_key,response)

        return response

    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))