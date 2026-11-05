"""AI hub › Agents and Models: agents in the store, models from the gateway's config."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flywheel_api.agents import Agents
from flywheel_api.app import create_app
from flywheel_api.gateway import Gateway
from flywheel_api.registry import Registry
from flywheel_api.store import FileStore

GATEWAY = Path(__file__).parent / "fixtures" / "gateway.yaml"
CODEX = {
    "name": "codex",
    "title": "Codex",
    "description": "OpenAI's coding agent, run headless with codex exec.",
    "framework": "Codex",
    "version": "0.154.0",
    "runner": {
        "type": "codex",
        "permission_mode": "bypassPermissions",
        "settings": {"model_provider": "gateway"},
        "env": {"OPENAI_API_KEY": "gateway-takes-no-key"},
    },
    "brain": {"instructions_file": "AGENTS.md", "skills_folder": ".agents/skills/"},
    "models": ["enmaas-glm-5-3", "enmaas-gpt-5-mini"],
    "default_model": "enmaas-glm-5-3",
}


def agents_on(root: Path, gateway: Path | None = GATEWAY) -> Agents:
    return Agents(FileStore(root), Gateway(gateway))


@pytest.fixture
def client(tmp_path) -> TestClient:
    store_root = tmp_path / "store"
    return TestClient(create_app(Registry(FileStore(store_root)), agents=agents_on(store_root)))


def test_the_models_are_the_gateways_routes_without_any_key(client):
    models = client.get("/api/models").json()
    assert [m["name"] for m in models] == ["enmaas-glm-5-3", "enmaas-gpt-5-mini", "unsloth-gemma4-26b-fast"]
    glm, mini, gemma = models
    assert glm == {
        "name": "enmaas-glm-5-3",
        "provider": "enmaas",
        "api_format": "OpenAI Chat",
        "model_id": "rits/zai-org/glm-5-3",
        "endpoint": {"url": "https://api.enmaas.devshift.net/v1", "from_environment": False},
        "price_input": 0,
        "price_output": 0,
        "max_input_tokens": 983040,
        "max_output_tokens": 65536,
        "used_by": [],
    }
    assert (mini["price_input"], mini["price_output"]) == (0.25, 2.0)
    assert gemma["endpoint"] == {"url": None, "from_environment": True}
    assert "ENMAAS_KEY" not in str(models) and "UNSLOTH" not in str(models)


def test_an_agent_is_added_read_and_listed(client):
    response = client.post("/api/agents", json=CODEX)
    assert response.status_code == 201, response.text
    assert response.json()["created"].endswith("Z")
    assert client.get("/api/agents/codex").json() == response.json()
    assert [a["name"] for a in client.get("/api/agents").json()] == ["codex"]
    used = {m["name"]: m["used_by"] for m in client.get("/api/models").json()}
    assert used == {"enmaas-glm-5-3": ["codex"], "enmaas-gpt-5-mini": ["codex"], "unsloth-gemma4-26b-fast": []}


def test_an_agent_is_never_changed(client):
    client.post("/api/agents", json=CODEX)
    response = client.post("/api/agents", json={**CODEX, "title": "Another"})
    assert response.status_code == 409
    assert client.get("/api/agents/codex").json()["title"] == "Codex"


@pytest.mark.parametrize(
    ("change", "detail"),
    [
        ({"models": ["enmaas-glm-5-3", "openai-gpt-9"]}, "the gateway routes no openai-gpt-9"),
        ({"default_model": "enmaas-gpt-6-sol"}, "default_model 'enmaas-gpt-6-sol' is not in models"),
        ({"name": "Codex_1"}, "name: Value error, an agent name is a DNS label"),
        ({"runner": {"type": "cursor"}}, "runner.type"),
        ({"runner": {"type": "codex", "env": {"OPENAI_API_KEY": "sk-live-123"}}}, "OPENAI_API_KEY names a key"),
        ({"models": []}, "models"),
        ({"surprise": 1}, "surprise"),
    ],
)
def test_a_refused_agent_says_why(client, change, detail):
    response = client.post("/api/agents", json={**copy.deepcopy(CODEX), **change})
    assert response.status_code == 422
    assert detail in response.json()["detail"]
    assert client.get("/api/agents").json() == []


def test_an_unknown_agent_is_404(client):
    assert client.get("/api/agents/nobody").status_code == 404
    assert client.get("/api/agents/Not_A_Name").status_code == 404


def test_without_a_gateway_config_models_and_new_agents_are_503(tmp_path):
    store_root = tmp_path / "store"
    client = TestClient(create_app(Registry(FileStore(store_root)), agents=agents_on(store_root, None)))
    assert client.get("/api/models").status_code == 503
    response = client.post("/api/agents", json=CODEX)
    assert (response.status_code, response.json()["detail"]) == (503, "the API has no gateway config: set FLYWHEEL_GATEWAY_CONFIG")


def test_without_agents_there_are_no_hub_routes(tmp_path):
    client = TestClient(create_app(Registry(FileStore(tmp_path))))
    assert client.get("/api/agents").status_code == 404
