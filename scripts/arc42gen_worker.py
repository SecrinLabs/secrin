"""
Run the arc42gen RQ worker.
Usage: poetry run arc42gen-worker

Uses SimpleWorker to avoid fork() — macOS ObjC runtime crashes
when forking after ObjC classes are initialized.
"""

import logging

from redis import Redis
from rq import SimpleWorker

from packages.config.settings import Settings


def main():
    """Start the arc42gen RQ worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    settings = Settings()
    redis_conn = Redis.from_url(settings.REDIS_URL)

    worker = SimpleWorker(["default"], connection=redis_conn)
    logging.getLogger(__name__).info("Starting RQ worker (Redis: %s)", settings.REDIS_URL)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
