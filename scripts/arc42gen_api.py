"""
Run the arc42gen API server.
Usage: poetry run arc42gen-api
"""

import logging
import uvicorn


def main():
    """Start the arc42gen API server."""
    # Configure root logger so all arc42gen logs are visible in the terminal
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    uvicorn.run(
        "packages.arc42gen.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
