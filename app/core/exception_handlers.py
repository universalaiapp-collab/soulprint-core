from fastapi import Request
from fastapi.responses import JSONResponse

async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests",
            "path": request.url.path
        },
    )
