"""JSON over HTTP(S) to EvalHub and MLflow, sent as the caller.

The API has no identity of its own there. It forwards the caller's Bearer
token (the dashboard user's, through the module's BFF), so EvalHub and
MLflow apply that user's rights, as the dashboard's own eval-hub pages do.
Both are services inside the cluster: no proxy, and no redirect is followed,
so the token never reaches another host.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

# Answers passed on as they are: the caller's own rights, or a missing object.
# Any other refusal is the API's or the service's fault, so it answers 502.
PASSED_ON = frozenset({401, 403, 404})


class RemoteError(Exception):
    """EvalHub or MLflow refused or failed a call; *status* is what the API answers."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urllib then raises the 3xx as an HTTPError


class Remote:
    def __init__(
        self,
        name: str,
        base_url: str,
        *,
        ca_file: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float = 30,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.headers = dict(headers or {})
        self.timeout = timeout
        context = ssl.create_default_context(cafile=ca_file)
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect, urllib.request.HTTPSHandler(context=context)
        )

    def json(self, method: str, path: str, token: str, *, query: Mapping | None = None, body: Any = None) -> Any:
        data = self.raw(method, path, token, query=query, body=body)
        return json.loads(data) if data else None

    def raw(self, method: str, path: str, token: str, *, query: Mapping | None = None, body: Any = None) -> bytes:
        url = self.base_url + path + ("?" + urllib.parse.urlencode(query) if query else "")
        headers = {**self.headers, "Accept": "application/json", "Authorization": f"Bearer {token}"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code if exc.code in PASSED_ON else 502
            raise RemoteError(status, f"{self.name} answered {exc.code}: {_message(exc.read())}") from exc
        except OSError as exc:  # URLError, a timeout, TLS
            raise RemoteError(502, f"{self.name} did not answer: {getattr(exc, 'reason', exc)}") from exc


def _message(body: bytes) -> str:
    """The service's own words: its JSON message, else the start of its text."""
    text = body.decode("utf-8", "replace").strip()
    try:
        data = json.loads(text)
    except ValueError:
        return text[:300] or "no body"
    if isinstance(data, dict):
        for key in ("message", "detail", "error"):
            if isinstance(data.get(key), str):
                return data[key]
    return text[:300]
