from sitemap.index import SitemapScraper, engine
from models.sitemap import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    scraper = SitemapScraper("https://cal.com/docs/sitemap.xml")
    scraper.scrape()
