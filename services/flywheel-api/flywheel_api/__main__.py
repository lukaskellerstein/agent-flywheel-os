"""Run the API: `python -m flywheel_api` in this folder.

Environment: the store (`store.store_from_env`: FLYWHEEL_STORE_DIR, or
BUCKET_NAME with S3_ENDPOINT_URL or BUCKET_HOST and BUCKET_PORT, and the
bucket's key as AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY), EvalHub and
MLflow for evaluations (`evaluations.evaluations_from_env`), the gateway's
config for AI hub › Models (FLYWHEEL_GATEWAY_CONFIG, a file path), and
FLYWHEEL_API_HOST (default 127.0.0.1; the image sets 0.0.0.0) and
FLYWHEEL_API_PORT (default 8080).
"""

import logging
import os
from pathlib import Path

import uvicorn

from .agents import Agents
from .app import create_app
from .evaluations import evaluations_from_env
from .gateway import Gateway
from .registry import Registry
from .store import store_from_env


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    store = store_from_env()
    registry = Registry(store)
    gateway_config = os.environ.get("FLYWHEEL_GATEWAY_CONFIG")
    agents = Agents(store, Gateway(Path(gateway_config) if gateway_config else None))
    app = create_app(registry, evaluations_from_env(registry, agents), agents)
    host = os.environ.get("FLYWHEEL_API_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=int(os.environ.get("FLYWHEEL_API_PORT", "8080")))


if __name__ == "__main__":
    main()
