"""JSON and bytes over HTTP(S) to the flywheel API and MLflow, as the loop.

The loop runs as its own ServiceAccount (deploy/flywheel/). Its token is
read from the file on every call, since the kubelet rotates it. Both
services are inside the cluster: no redirect is followed, so the token
never reaches another host.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any

TIMEOUT_S = 120


class HttpError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Http:
    def __init__(
        self,
        name: str,
        base_url: str,
        token_file: Path,
        ca_file: str | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.token_file = token_file
        self.headers = dict(headers or {})
        context = ssl.create_default_context(cafile=ca_file) if ca_file else None
        self._opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=context))

    def json(self, method: str, path: str, body: Any = None, query: Mapping[str, Any] | None = None) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        answer = self.raw(method, path, data, query, "application/json" if data is not None else None)
        return json.loads(answer) if answer else None

    def raw(
        self,
        method: str,
        path: str,
        data: bytes | None = None,
        query: Mapping[str, Any] | None = None,
        content_type: str | None = None,
    ) -> bytes:
        url = self.base_url + path + (f"?{urllib.parse.urlencode(query)}" if query else "")
        headers = {**self.headers, "Authorization": f"Bearer {self.token_file.read_text().strip()}"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with self._opener.open(request, timeout=TIMEOUT_S) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise HttpError(exc.code, f"{self.name} {method} {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise HttpError(503, f"{self.name} {method} {path}: {exc.reason}") from exc
