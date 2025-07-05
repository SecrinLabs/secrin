from packages.scraper.src.sitemap.index import SitemapScraper
from packages.scraper.src.githubissue.index import GithubScraper
from packages.scraper.src.gitcommit.index import GitScraper

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
