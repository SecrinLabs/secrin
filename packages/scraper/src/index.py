from sitemap.index import SitemapScraper
from githubissue.index import GithubScraper
from gitcommit.index import GitScraper
from models.sitemap import Base
from models.githubissue import Base
from models import engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

    # sitemap
    scraper = SitemapScraper("https://cal.com/docs/sitemap.xml")
    scraper.scrape()

    # github issue
    TOKEN = "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"  # replace securely in real use
    scraper = GithubScraper(TOKEN, "calcom", "cal.com")
    scraper.scrape()

    # local git history
    scraper = GitScraper("/Users/jenil/Documents/cal.com")
    scraper.scrape(branch="main", max_count=1000)