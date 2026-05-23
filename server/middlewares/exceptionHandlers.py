from fastapi import Request
from fastapi.responses import JSONResponse
from logger import Logger


async def catch_exception_from_middleware(request, call_next):
    try:
        response = await call_next(Request)
        return response
    except Exception as e:
        Logger.exception(f"UNHANDLED EXCEPTION for: {str(e)}")
        return JSONResponse(
            status_code=500, content={"message": "An internal server error occurred."}
        )
