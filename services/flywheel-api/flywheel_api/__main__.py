"""Run the API: `python -m flywheel_api` in this folder.

Environment: the store (`store.store_from_env`: FLYWHEEL_STORE_DIR, or
BUCKET_NAME with S3_ENDPOINT_URL or BUCKET_HOST and BUCKET_PORT, and the
bucket's key as AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY), and
FLYWHEEL_API_HOST (default 127.0.0.1; the image sets 0.0.0.0) and
FLYWHEEL_API_PORT (default 8080).
"""

import logging
import os

import uvicorn

from .app import create_app
from .registry import Registry
from .store import store_from_env


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = create_app(Registry(store_from_env()))
    host = os.environ.get("FLYWHEEL_API_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=int(os.environ.get("FLYWHEEL_API_PORT", "8080")))


if __name__ == "__main__":
    main()
