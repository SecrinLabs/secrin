from service.src.integrations.sitemap import SitemapScraper
from service.src.integrations.github import GithubScraper

class ScraperFactory:
    @staticmethod
    def create_scraper(integration_name, config):
        if integration_name == "sitemap":
            return SitemapScraper(config["sitemapUrl"])
        elif integration_name == "github":
            return GithubScraper(config["token"], config["repoUrl"])
        # elif integration_name == "gitlocal":
        #     return GitScraper(config["repo_path"])
        else:
            raise ValueError(f"Unknown integration: {integration_name}")
