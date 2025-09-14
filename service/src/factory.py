from service.src.integrations.github import GithubScraper
from db.index import SessionLocal

from db.models.integration import IntegrationType
from db.models.repository import Repository

from api.utils.github_token import get_github_access_token

class ScraperFactory:
    @staticmethod
    def create_scraper(integration_type, config, user_id):
        session = SessionLocal()
        if integration_type == IntegrationType.github:
            repoURLs = session.query(Repository).filter(Repository.user_id == user_id).first()
            token = get_github_access_token(config["installation_token"])
            return GithubScraper(token, repoURLs.repo_url, user_id)
        else:
            raise ValueError(f"Unknown integration: {integration_type}")
