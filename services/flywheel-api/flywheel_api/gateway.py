"""The models an agent may use: the routes of the cluster's LiteLLM gateway,
read from the gateway's own config (deploy/gateway/config/litellm.yaml,
mounted read-only), so a model is listed exactly when the gateway routes it.

The file holds no key: its `api_key` fields name environment variables of
the gateway's pod. Only the fields below leave this module, so neither a key
nor its variable's name is ever answered.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from .problems import Unavailable

PER_MILLION = 1_000_000
FROM_ENV = "os.environ/"
# LiteLLM's provider prefix of `litellm_params.model`, as the dialect the gateway speaks to it.
API_FORMATS = {"openai": "OpenAI Chat", "anthropic": "Anthropic Messages"}


class Gateway:
    def __init__(self, config_path: Path | None):
        self.config_path = config_path

    def models(self) -> list[dict]:
        """Every alias the gateway routes, in its config's order. The file is
        read on every call: a changed ConfigMap reaches the mount within a minute."""
        if self.config_path is None:
            raise Unavailable("the API has no gateway config: set FLYWHEEL_GATEWAY_CONFIG")
        data = yaml.safe_load(self.config_path.read_text()) or {}
        return [_model(entry) for entry in data.get("model_list") or []]

    def names(self) -> list[str]:
        return [model["name"] for model in self.models()]


def _model(entry: Mapping[str, Any]) -> dict:
    params = entry.get("litellm_params") or {}
    info = entry.get("model_info") or {}
    prefix, _, model_id = str(params.get("model", "")).partition("/")
    name = entry["model_name"]
    return {
        "name": name,
        # The aliases are named <provider>-<model> (enmaas-glm-5-3, unsloth-…).
        "provider": name.split("-", 1)[0],
        "api_format": API_FORMATS.get(prefix, prefix),
        "model_id": model_id,
        "endpoint": _endpoint(params.get("api_base")),
        "price_input": _per_million(params.get("input_cost_per_token")),
        "price_output": _per_million(params.get("output_cost_per_token")),
        "max_input_tokens": info.get("max_input_tokens"),
        "max_output_tokens": info.get("max_output_tokens"),
    }


def _endpoint(api_base: Any) -> dict | None:
    """A URL, or that the gateway's environment sets it (a local engine, the laptop only)."""
    if not isinstance(api_base, str):
        return None
    if api_base.startswith(FROM_ENV):
        return {"url": None, "from_environment": True}
    return {"url": api_base, "from_environment": False}


def _per_million(cost_per_token: Any) -> float | None:
    if isinstance(cost_per_token, bool) or not isinstance(cost_per_token, int | float):
        return None
    return round(cost_per_token * PER_MILLION, 6)
