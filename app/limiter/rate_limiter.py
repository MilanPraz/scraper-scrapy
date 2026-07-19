from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request
# This limits by user IP address.
limiter=Limiter(key_func=get_remote_address
                ,default_limits=["1000 per day","100 per hour"])

# async def rate_limit_exceeded_handler(request: Request, exc: Exception):
#     return await _rate_limit_exceeded_handler(request, exc)  # type: ignore[arg-type]


async def rate_limit_exceeded_handler(
    request: Request,
    exc: Exception,
):
    return _rate_limit_exceeded_handler(
        request,
        exc,  # type: ignore[arg-type]
    )