from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from ..logger import logger


async def catch_exception_from_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        logger.exception(f"VALIDATION ERROR: {e}")
        return JSONResponse(
            status_code=422,
            content={"detail": e.errors(), "message": "Input validation failed"}
        )
    except Exception as e:
        logger.exception(f"UNHANDLED EXCEPTION for: {str(e)}")
        return JSONResponse(
            status_code=500, content={"message": "An internal server error occurred."}
        )
