from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from packages.config.settings import Settings
from apps.api.utils import APIResponse, APIException
from apps.api.routes import api_router

settings = Settings()

app = FastAPI(
    title="Secrin API",
    description="Secrin Backend API",
    version="0.1.0"
)


# Global exception handler
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.get("/")
async def welcome():
    """Welcome endpoint"""
    return APIResponse.success(
        data={"version": "0.1.0"},
        message="Welcome to Secrin API"
    )


# Include all API routes
app.include_router(api_router)