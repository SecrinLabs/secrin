from service.src.factory import ScraperFactory

from db.index import SessionLocal
from db.models.integration import Integration, IntegrationType
from config import get_logger

# Setup logger for this module
logger = get_logger(__name__)

def run_scraper_by_name(scraper_name: IntegrationType, user_id: int):
    """Run a single scraper by integration name."""
    session = SessionLocal()
    try:
        integration = session.query(Integration).filter(Integration.user_id == user_id, Integration.type == scraper_name).first()

        if not integration:
            raise ValueError(f"No connected integration found with name: {scraper_name}")
        scraper = ScraperFactory.create_scraper(integration.type, integration.config, user_id)
        scraper.scrape()
    finally:
        session.close()