from packages.scraper.src.store.sitemap import SitemapScraper
from packages.scraper.src.store.githubissue import GithubScraper
from packages.scraper.src.store.gitcommit import GitScraper

class ScraperFactory:
    @staticmethod
    def create_scraper(integration_name, config):
        if integration_name == "sitemap":
            return SitemapScraper(config["url"])
        elif integration_name == "github":
            return GithubScraper(config["token"], config["owner"], config["repo"])
        elif integration_name == "localgit":
            return GitScraper(config["repo_path"])
        else:
            raise ValueError(f"Unknown integration: {integration_name}")
