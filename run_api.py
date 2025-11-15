"""
Simple script to run the Secrin API server
"""
import uvicorn
from packages.config.settings import Settings

settings = Settings()

if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
