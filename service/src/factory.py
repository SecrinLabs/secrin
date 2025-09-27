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
            # Query all repositories for the user (previously we only grabbed the first)
            repo_objs = session.query(Repository).filter(Repository.user_id == user_id).all()
            token = get_github_access_token(config["installation_token"])

            if not repo_objs:
                session.close()
                raise ValueError(f"No repositories found for user_id={user_id}")

            # Create a GithubScraper per repository. If any init fails, log and skip that repo.
            scrapers = []
            for repo in repo_objs:
                try:
                    scrapers.append(GithubScraper(token, repo.repo_url, user_id))
                except Exception as e:
                    # Don't let one bad repo stop the rest; print for visibility.
                    print(f"⚠️ Skipping repo {repo.repo_url}: {e}")

            session.close()

            if not scrapers:
                raise ValueError(f"No valid Github scrapers could be created for user_id={user_id}")

            # If there's only one scraper, return it for backward compatibility. Otherwise return a composite.
            if len(scrapers) == 1:
                return scrapers[0]
            else:
                return MultiScraper(scrapers)
        else:
            raise ValueError(f"Unknown integration: {integration_type}")


class MultiScraper:
    """Simple composite that runs multiple scrapers sequentially via a single scrape() call.

    This keeps backward compatibility with callers that expect an object with a scrape() method.
    """
    def __init__(self, scrapers):
        self.scrapers = scrapers

    def scrape(self):
        for s in self.scrapers:
            try:
                s.scrape()
            except Exception as e:
                # Log the error and continue with other scrapers
                print(f"❌ Scraper failed for {getattr(s, 'repo', getattr(s, 'owner', 'unknown'))}: {e}")
