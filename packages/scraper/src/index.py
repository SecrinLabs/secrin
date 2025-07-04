from packages.scraper.src.sitemap.index import SitemapScraper
from packages.scraper.src.githubissue.index import GithubScraper
from packages.scraper.src.gitcommit.index import GitScraper
from packages.scraper.src.models.sitemap import Base
from packages.scraper.src.models.githubissue import Base
from packages.scraper.src.models import engine

def run_all_scrapers():
    Base.metadata.create_all(bind=engine)

    run_sitemap()
    run_github()
    run_localgit()

def run_sitemap():
    # sitemap
    scraper = SitemapScraper("https://cal.com/docs/sitemap.xml")
    scraper.scrape()

def run_github():
    # github issue
    TOKEN = "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"  # replace securely in real use
    scraper = GithubScraper(TOKEN, "calcom", "cal.com")
    scraper.scrape()

def run_localgit():
    # local git history
    scraper = GitScraper("/Users/jenil/Documents/cal.com")
    scraper.scrape(branch="main", max_count=1000)

if __name__ == "__main__":
    run_all_scrapers()