"""
Simple script to run the Secrin API server
"""
import uvicorn
from packages.config.settings import Settings

def main():
    settings = Settings()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False
    )

if __name__ == "__main__":
    main()
