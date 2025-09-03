from src.integrations.sitemap import SitemapScraper
from src.integrations.github import GithubScraper

class ScraperFactory:
    @staticmethod
    def create_scraper(integration_name, config):
        if integration_name == "sitemap":
            return SitemapScraper(config["sitemapUrl"])
        elif integration_name == "github":
            return GithubScraper(config["token"], config["repoUrl"], limit=config["limit"])
        else:
            raise ValueError(f"Unknown integration: {integration_name}")
