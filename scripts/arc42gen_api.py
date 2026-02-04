"""
Run the arc42gen API server.
Usage: poetry run arc42gen-api
"""

import uvicorn


def main():
    """Start the arc42gen API server."""
    uvicorn.run(
        "packages.arc42gen.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
