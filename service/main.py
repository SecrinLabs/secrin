from service.src.factory import ScraperFactory
from service.src.db import SessionLocal
from service.src.models.Integration import Integration
from service.src.models import Base, engine

def run_all_scrapers():
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        integrations = session.query(Integration).filter_by(IsOpen=True).all()
        for integration in integrations:
            try:
                scraper = ScraperFactory.create_scraper(integration.Name, integration.Config)
                scraper.scrape()  # Always call with no arguments; defaults handled in class
            except Exception as e:
                print(f"Failed to run scraper for {integration.Name}: {e}")
    finally:
        session.close()

def run_scraper_by_name(scraper_name: str):
    """Run a single scraper by integration name."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        integration = session.query(Integration).filter_by(name=scraper_name, IsOpen=True).first()
        if not integration:
            raise ValueError(f"No connected integration found with name: {scraper_name}")
        scraper = ScraperFactory.create_scraper(integration.Name, integration.Config)
        scraper.scrape()
    finally:
        session.close()

if __name__ == "__main__":
    run_all_scrapers()