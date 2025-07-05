from packages.scraper.src.factory import ScraperFactory
from packages.db.db import SessionLocal
from packages.models.integrations import Integration
from packages.models import Base, engine

def run_all_scrapers():
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        integrations = session.query(Integration).filter_by(is_connected=True).all()
        for integration in integrations:
            try:
                scraper = ScraperFactory.create_scraper(integration.name, integration.config)
                scraper.scrape()  # Always call with no arguments; defaults handled in class
            except Exception as e:
                print(f"Failed to run scraper for {integration.name}: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    run_all_scrapers()