from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.domain.errors import MarketDataError


async def market_data_error_handler(_request: Request, exception: MarketDataError) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content=jsonable_encoder(
            {
                "error": {
                    "code": exception.code,
                    "message": exception.message,
                    "details": exception.details,
                }
            }
        ),
    )
