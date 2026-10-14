#!/usr/bin/env python3
"""Probe EnMaaS: which models answer, in which API dialect, how fast, at what price.

EnMaaS, Red Hat Engineering's AI gateway (docs/research.md "EnMaaS"), serves
three dialects at one base URL: OpenAI Chat Completions, OpenAI Responses and
Anthropic Messages. Its /v1/models catalog leaves models out, so a model is
known to work only once a call to it answers.

Run it where the key is. In the cluster, with the gateway's key:

    oc exec -i -n agent-flywheel deploy/gateway -- python3 - [args] < scripts/enmaas/probe.py

On the Mac, with ENMAAS_KEY from ~/Projects/.envrc:

    scripts/enmaas/probe.py [args]

Through the gateway, with its aliases (enmaas-gpt-5-mini and the others) as
the model ids; the gateway has no master key, so any key passes:

    oc exec -i -n agent-flywheel deploy/gateway -- env ENMAAS_BASE_URL=http://localhost:4000/v1 \\
        python3 - --stage dialects --dialect-models enmaas-gpt-5-mini < scripts/enmaas/probe.py

Stages, the first three by default (--stage picks some):

    catalog   GET /v1/models with both auth headers. Free.
    models    one call per candidate id, in its family's dialect, at most 16
              output tokens. An id that does not exist answers 404 and costs
              nothing; one that exists costs a few tokens.
    dialects  for a few models (--dialect-models, or GLM plus the first OpenAI
              and Claude ids that answered): every dialect, plain, with a tool,
              and with a tool streamed, as the agents call it. At most 512
              output tokens a call.
    speed     for every candidate that answers: 3 streamed answers of about
              300 words, in its own dialect, at its lowest reasoning level.
              Time to the first token, tokens per second, and the list price
              from LiteLLM's table where LiteLLM is installed. About 450 output
              tokens a call, so about 0.4 USD for every model EnMaaS serves.
              It writes scripts/enmaas/models.md:

    oc exec -i -n agent-flywheel deploy/gateway -- python3 - --stage catalog --stage speed < scripts/enmaas/probe.py > scripts/enmaas/models.md

Only GLM 5.3 has no usage cost; every other call counts against the key
owner's Red Hat AI budget. The key is read from ENMAAS_KEY and never printed.
"""

import argparse
import importlib.util
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone

BASE = os.environ.get("ENMAAS_BASE_URL", "https://api.enmaas.devshift.net/v1").rstrip("/")
GLM = "rits/zai-org/glm-5-3"

# Newest first. EnMaaS hands an id it does not route itself to OpenAI's API,
# so an id that does not exist answers 404 model_not_found from OpenAI. GPT 6
# answers only under a code name (gpt-6-sol; plain gpt-6 is a 404), and no
# list names them: these are the ones found by guessing on 2026-10-14. The
# -pro models exist too (gpt-5.5-pro and older, o3-pro, o1-pro) but refuse
# a low reasoning level and cost far more, so they are left out.
OPENAI = [
    "gpt-6.1-sol", "gpt-6-sol", "gpt-6-astra", "gpt-6-luna", "gpt-5.6-luna",
    "gpt-5.6", "gpt-5.6-mini", "gpt-5.6-nano", "gpt-5.6-codex",
    "gpt-5.5", "gpt-5.5-mini", "gpt-5.5-nano", "gpt-5.5-codex",
    "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.3-codex",
    "gpt-5.2", "gpt-5.2-codex", "gpt-5.1", "gpt-5.1-codex", "gpt-5.1-codex-mini",
    "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-codex",
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini",
    "o3", "o4-mini", "o3-mini", "o1",
    "gpt-oss-120b", "gpt-oss-20b",
]
# The Claude ids the dialect stage prefers, best first.
CLAUDE_PICK = ["claude-sonnet-5-5", "claude-opus-5-5", "claude-sonnet-5", "claude-opus-5"]

PATH = {"chat": "/chat/completions", "responses": "/responses", "messages": "/messages"}
DIALECTS = tuple(PATH)
STREAM_END = {"chat": "[DONE]", "responses": "response.completed", "messages": "message_stop"}
STREAM_TOOL = {"chat": '"tool_calls"', "responses": '"function_call"', "messages": '"tool_use"'}
RATE_HEADERS = ("x-ratelimit", "anthropic-ratelimit", "retry-after")

PROMPT = "Reply with exactly: OK"
TOOL_PROMPT = "What is the weather in Brno? Answer only by calling the get_weather tool."
SPEED_PROMPT = "Explain in about 300 words how a lighthouse works. Plain prose: no lists, no headings."
SPEED_RUNS = 3
SPEED_MAX_OUT = 2048
TOOL = {
    "name": "get_weather",
    "description": "The current weather in a city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}


@dataclass
class Result:
    model: str
    dialect: str
    status: int | None
    seconds: float
    data: dict = field(default_factory=dict)
    raw: str = ""
    rate: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300


def bare(model: str) -> str:
    """The model id behind one of the gateway's aliases (enmaas-gpt-5-mini)."""
    return model.removeprefix("enmaas-")


def family(model: str) -> str:
    model = bare(model)
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gemini-"):
        return "gemini"
    if model.startswith(("rits/", "glm-")):
        return "rits"
    return "openai"


def native_dialect(model: str) -> str:
    # Responses for OpenAI: the -codex models answer nowhere else.
    return {"anthropic": "messages", "openai": "responses"}.get(family(model), "chat")


def headers(dialect: str) -> dict:
    key = os.environ.get("ENMAAS_KEY", "")
    if not key:
        sys.exit("probe: ENMAAS_KEY is not set")
    if dialect == "messages":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    return {"Authorization": f"Bearer {key}"}


def openai_reasoning(model: str) -> bool:
    """The o series and GPT 5 and later: they take a reasoning level."""
    version = re.match(r"gpt-(\d+)", bare(model))
    return family(model) == "openai" and (
        bool(re.match(r"o\d", bare(model))) or (version is not None and int(version.group(1)) >= 5))


def body(model: str, dialect: str, content: str, *, tool: bool, stream: bool, max_out: int,
         effort: str | None) -> dict:
    # A reasoning level goes only to the models that take one; None sends none.
    takes = openai_reasoning(model) or (family(model) == "gemini" and dialect == "chat")
    effort = effort if takes else None
    if dialect == "chat":
        # OpenAI's reasoning models refuse max_tokens on Chat Completions.
        limit = "max_completion_tokens" if family(model) == "openai" else "max_tokens"
        b = {"model": model, "messages": [{"role": "user", "content": content}], limit: max_out}
        if tool:
            b["tools"] = [{"type": "function", "function": TOOL}]
        if effort:
            b["reasoning_effort"] = effort
    elif dialect == "responses":
        b = {"model": model, "input": content, "max_output_tokens": max(max_out, 16)}
        if tool:
            b["tools"] = [{"type": "function", **TOOL}]
        if effort:
            b["reasoning"] = {"effort": effort}
    else:
        b = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": max_out}
        if tool:
            b["tools"] = [{
                "name": TOOL["name"],
                "description": TOOL["description"],
                "input_schema": TOOL["parameters"],
            }]
    if stream:
        b["stream"] = True
    return b


def request(dialect: str, payload: dict) -> urllib.request.Request:
    return urllib.request.Request(
        BASE + PATH[dialect],
        data=json.dumps(payload).encode(),
        headers={**headers(dialect), "content-type": "application/json"},
    )


def call(model: str, dialect: str, *, tool=False, stream=False, max_out=16, effort="low") -> Result:
    content = TOOL_PROMPT if tool else PROMPT
    payload = body(model, dialect, content, tool=tool, stream=stream, max_out=max_out, effort=effort)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request(dialect, payload), timeout=180) as response:
            status, hdrs, raw = response.status, response.headers, response.read()
    except urllib.error.HTTPError as err:
        status, hdrs, raw = err.code, err.headers, err.read()
    except (urllib.error.URLError, TimeoutError) as err:
        return Result(model, dialect, None, time.monotonic() - start, raw=str(err))
    text = raw.decode("utf-8", "replace")
    rate = {k.lower(): v for k, v in hdrs.items() if k.lower().startswith(RATE_HEADERS)}
    data = {}
    if not stream:
        try:
            data = json.loads(text)
        except ValueError:
            pass
    return Result(model, dialect, status, time.monotonic() - start, data, text, rate)


def error_of(r: Result) -> str:
    if r.status is None:
        return r.raw[:120]
    err = r.data.get("error") if isinstance(r.data, dict) else None
    if isinstance(err, dict):
        return f"{err.get('code') or err.get('type')}: {err.get('message', '')}"[:120]
    return " ".join(r.raw.split())[:120]


def usage_of(r: Result) -> tuple[int, int]:
    u = r.data.get("usage") or {}
    if r.dialect == "chat":
        return u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    return u.get("input_tokens", 0), u.get("output_tokens", 0)


def text_of(r: Result) -> str:
    d = r.data
    if r.dialect == "chat":
        return (d.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    if r.dialect == "responses":
        return "".join(
            c.get("text", "")
            for o in d.get("output", []) if o.get("type") == "message"
            for c in o.get("content", []) if c.get("type") == "output_text"
        )
    return "".join(c.get("text", "") for c in d.get("content", []) if c.get("type") == "text")


def tool_called(r: Result) -> bool:
    d = r.data
    if r.dialect == "chat":
        return bool((d.get("choices") or [{}])[0].get("message", {}).get("tool_calls"))
    if r.dialect == "responses":
        return any(o.get("type") == "function_call" for o in d.get("output", []))
    return any(c.get("type") == "tool_use" for c in d.get("content", []))


def table(head: list[str], rows: list[list]) -> None:
    print("| " + " | ".join(head) + " |")
    print("|" + "|".join(":--" for _ in head) + "|")
    for row in rows:
        print("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |")
    print()


def get_catalog() -> list[str]:
    print("## Catalog: GET /v1/models\n")
    ids: list[str] = []
    for dialect, auth in (("chat", "Authorization: Bearer"), ("messages", "x-api-key")):
        request = urllib.request.Request(BASE + "/models", headers=headers(dialect))
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                listed = [m["id"] for m in json.load(response).get("data", [])]
        except (urllib.error.URLError, ValueError) as err:
            print(f"- {auth}: failed, {err}")
            continue
        print(f"- {auth}: {len(listed)} ids: {', '.join(listed)}")
        ids += [m for m in listed if m not in ids]
    print()
    return ids


def probe_models(candidates: list[str], workers: int) -> list[Result]:
    print(f"## Models: one call each in its own dialect, {len(candidates)} ids\n")
    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(lambda m: call(m, native_dialect(m)), candidates))
    rows = []
    for r in sorted(results, key=lambda r: (not r.ok, family(r.model))):
        tokens = "%d/%d" % usage_of(r) if r.ok else ""
        served = r.data.get("model", "") if r.ok else ""
        rows.append([r.model, r.dialect, r.status, served, tokens, f"{r.seconds:.1f}",
                     "" if r.ok else error_of(r)])
    table(["id", "dialect", "status", "served as", "tokens in/out", "s", "error"], rows)
    return results


def probe_dialects(models: list[str]) -> list[Result]:
    print(f"## Dialects: {', '.join(models)}\n")
    results, rows = [], []
    for model in models:
        for dialect in DIALECTS:
            plain = call(model, dialect, max_out=512)
            results.append(plain)
            if not plain.ok:
                rows.append([model, dialect, plain.status, "", "", "", error_of(plain)])
                continue
            effort = "low"
            tool = call(model, dialect, tool=True, max_out=512)
            if dialect == "chat" and tool.status == 400 and "reasoning_effort" in tool.raw:
                # gpt-5.5 and later: tools on Chat Completions only without reasoning.
                effort = "none"
                results.append(tool)
                tool = call(model, dialect, tool=True, max_out=512, effort=effort)
            stream = call(model, dialect, tool=True, stream=True, max_out=512, effort=effort)
            results += [tool, stream]
            streamed = (
                f"{stream.raw.count('data:')} events"
                f"{', tool' if STREAM_TOOL[dialect] in stream.raw else ', no tool'}"
                f"{', ended' if STREAM_END[dialect] in stream.raw else ', no end'}"
                if stream.ok else f"{stream.status} {error_of(stream)}"
            )
            called = "yes" if tool_called(tool) else (
                f"no ({tool.status} {error_of(tool) if not tool.ok else ''})")
            if effort == "none" and tool_called(tool):
                called += ", reasoning_effort none only"
            rows.append([model, dialect, plain.status, repr(text_of(plain)[:30]), called, streamed, ""])
    table(["model", "dialect", "plain", "text", "tool call", "tool, streamed", "error"], rows)
    return results


def print_rates(results: list[Result]) -> None:
    seen = {}
    for r in results:
        if r.rate and family(r.model) not in seen:
            seen[family(r.model)] = (r.model, r.rate)
    if not seen:
        print("## Rate limit headers: none in any answer\n")
        return
    print("## Rate limit headers, one answer per family\n")
    for fam, (model, rate) in seen.items():
        print(f"- {fam} ({model}): " + ", ".join(f"{k}={v}" for k, v in sorted(rate.items())))
    print()


def print_tokens(results: list[Result]) -> None:
    spent: dict[str, list[int]] = {}
    for r in results:
        if r.ok and r.data.get("usage") is not None:
            i, o = usage_of(r)
            spent.setdefault(r.model, [0, 0])
            spent[r.model][0] += i
            spent[r.model][1] += o
    streamed = sum(1 for r in results if r.ok and not r.data)
    print("## Tokens this run, by model (streamed calls not counted: %d)\n" % streamed)
    table(["model", "in", "out"], [[m, i, o] for m, (i, o) in sorted(spent.items())])


@dataclass
class Speed:
    status: int | None
    effort: str | None
    first: float | None = None  # seconds to the first streamed token, text or reasoning
    seconds: float = 0.0  # the whole call
    tokens_in: int = 0
    tokens_out: int = 0
    reasoning: int = 0
    streamed_reasoning: bool = False
    error: str = ""

    @property
    def rate(self) -> float | None:
        """The tokens the stream showed, over the time it showed them.

        OpenAI streams no reasoning: its reasoning tokens ran before the first
        token, so they are left out, or a model that thinks looks faster.
        """
        shown = self.tokens_out if self.streamed_reasoning else self.tokens_out - self.reasoning
        if self.first is None or shown <= 0 or self.seconds <= self.first:
            return None
        return shown / (self.seconds - self.first)


def stream_event(dialect: str, event: dict, run: Speed) -> str | None:
    """Fold one stream event's usage into run; return the kind of token it carries."""
    kind = event.get("type", "")
    if dialect == "chat":
        usage = event.get("usage") or {}
        if usage:
            run.tokens_in = usage.get("prompt_tokens", 0)
            run.tokens_out = usage.get("completion_tokens", 0)
            run.reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        delta = ((event.get("choices") or [{}])[0] or {}).get("delta") or {}
        if delta.get("content"):
            return "text"
        if delta.get("reasoning_content") or delta.get("reasoning"):
            return "reasoning"
    elif dialect == "responses":
        if kind in ("response.completed", "response.incomplete"):
            usage = event.get("response", {}).get("usage") or {}
            run.tokens_in = usage.get("input_tokens", 0)
            run.tokens_out = usage.get("output_tokens", 0)
            run.reasoning = (usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0
        if kind == "response.output_text.delta":
            return "text"
        if kind.startswith("response.reasoning") and kind.endswith(".delta"):
            return "reasoning"
    elif kind == "message_start":
        run.tokens_in = event.get("message", {}).get("usage", {}).get("input_tokens", 0)
    elif kind == "message_delta":
        run.tokens_out = event.get("usage", {}).get("output_tokens", run.tokens_out)
    elif kind == "content_block_delta":
        return {"text_delta": "text", "thinking_delta": "reasoning"}.get(
            event.get("delta", {}).get("type"))
    return None


def stream_once(model: str, dialect: str, effort: str | None) -> Speed:
    payload = body(model, dialect, SPEED_PROMPT, tool=False, stream=True,
                   max_out=SPEED_MAX_OUT, effort=effort)
    if dialect == "chat":
        payload["stream_options"] = {"include_usage": True}
    run = Speed(None, effort)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request(dialect, payload), timeout=300) as response:
            run.status = response.status
            for line in response:
                text = line.decode("utf-8", "replace").strip()
                if not text.startswith("data:") or text[5:].strip() == "[DONE]":
                    continue
                try:
                    event = json.loads(text[5:])
                except ValueError:
                    continue
                kind = stream_event(dialect, event, run)
                if kind and run.first is None:
                    run.first = time.monotonic() - start
                run.streamed_reasoning |= kind == "reasoning"
    except urllib.error.HTTPError as err:
        run.status = err.code
        # Whole: the word that names the refused field can come late in it.
        run.error = " ".join(err.read().decode("utf-8", "replace").split())
    except (urllib.error.URLError, TimeoutError) as err:
        run.error = str(err)[:160]
    run.seconds = time.monotonic() - start
    if family(model) == "gemini":
        # Vertex counts the thinking apart from completion_tokens (673 against
        # 375 measured); OpenAI counts it inside. Count it inside for both.
        run.tokens_out += run.reasoning
    return run


def efforts(model: str) -> list[str | None]:
    """The reasoning levels to try, lowest first; None sends no level."""
    if openai_reasoning(model):
        return ["none", "minimal", "low"]
    if family(model) == "gemini":
        return ["none", "low", None]
    return [None]


def measure(model: str) -> list[Speed]:
    dialect = native_dialect(model)
    for effort in efforts(model):
        run = stream_once(model, dialect, effort)
        refused = run.status == 400 and any(
            word in run.error.lower() for word in ("reasoning", "effort", "thinking"))
        if not (refused and effort is not None):
            break
    if run.status != 200:
        return [run]
    return [run] + [stream_once(model, dialect, run.effort) for _ in range(SPEED_RUNS - 1)]


def list_prices() -> dict:
    """LiteLLM's own price table, where LiteLLM is installed (the gateway pod)."""
    spec = importlib.util.find_spec("litellm")
    if not spec or not spec.origin:
        return {}
    path = os.path.join(os.path.dirname(spec.origin), "model_prices_and_context_window_backup.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def price(prices: dict, model: str) -> tuple[float, float] | None:
    """USD per million tokens in and out."""
    if model == GLM:
        return 0.0, 0.0
    for key in (model, f"vertex_ai/{model}", f"gemini/{model}", f"anthropic/{model}"):
        entry = prices.get(key) or {}
        if entry.get("input_cost_per_token") is not None and entry.get("output_cost_per_token") is not None:
            return entry["input_cost_per_token"] * 1e6, entry["output_cost_per_token"] * 1e6
    return None


def probe_speed(candidates: list[str], workers: int) -> None:
    print(f"## Speed and price: {SPEED_RUNS} streamed answers each, about 300 words\n")
    print(
        "Each id is called from where this probe runs, in its own dialect (Responses for\n"
        "OpenAI, Messages for Claude, Chat Completions for the rest), at the lowest\n"
        "reasoning level it takes. *First token*: seconds to the first streamed token,\n"
        "text or reasoning. *Tokens/s*: the tokens the stream showed, over the time from\n"
        "the first token to the end; OpenAI's hidden reasoning tokens are left out. The\n"
        "median of the answers, and the slowest and fastest of them. *Price*: USD per\n"
        "million tokens, LiteLLM's list price; EnMaaS shows none, and only GLM 5.3 is\n"
        "free. Models run 4 at a time, so the numbers include EnMaaS under that load.\n"
        f"*(cut)*: an answer hit the limit of {SPEED_MAX_OUT} output tokens.\n"
    )
    with ThreadPoolExecutor(workers) as pool:
        measured = dict(zip(candidates, pool.map(measure, candidates)))
    prices = list_prices()
    rows, missing, spent, unpriced = [], [], 0.0, []
    for model, runs in measured.items():
        done = [r for r in runs if r.status == 200 and r.tokens_out]
        if not done:
            missing.append([model, runs[0].status,
                            runs[0].error[:160] or "no tokens in the answer"])
            continue
        rates = [r.rate for r in done if r.rate]
        cost = price(prices, model)
        if cost:
            spent += sum(r.tokens_in * cost[0] + r.tokens_out * cost[1] for r in done) / 1e6
        else:
            unpriced.append(model)
        rows.append((statistics.median(rates) if rates else 0.0, [
            model, family(model), native_dialect(model), done[0].effort or "-",
            "%.2f" % statistics.median(r.first or 0 for r in done),
            "%.0f" % statistics.median(rates) if rates else "-",
            "%.0f-%.0f" % (min(rates), max(rates)) if rates else "-",
            "%.1f" % statistics.median(r.seconds for r in done),
            "%d" % statistics.median(r.tokens_out for r in done)
            + (" (cut)" if any(r.tokens_out >= SPEED_MAX_OUT for r in done) else ""),
            "%d" % statistics.median(r.reasoning for r in done),
            "%g" % cost[0] if cost else "?", "%g" % cost[1] if cost else "?",
        ]))
    table(["model", "family", "dialect", "reasoning level", "first token s", "tokens/s",
           "slowest-fastest", "answer s", "out tokens", "of them reasoning", "USD/M in",
           "USD/M out"], [row for _, row in sorted(rows, key=lambda r: -r[0])])
    absent = [m for m, status, _ in missing if status in (403, 404)]
    if absent:
        print(f"Not on EnMaaS for this key (404 or 403): {', '.join(absent)}.\n")
    failed = [row for row in missing if row[1] not in (403, 404)]
    if failed:
        print("Not measured: the call failed.\n")
        table(["id", "status", "error"], failed)
    print(f"This stage spent about {spent:.2f} USD at list price"
          + (f", plus the tokens of {len(unpriced)} models with no price in the table: "
             f"{', '.join(unpriced)}." if unpriced else "."))
    print()


def pick(results: list[Result], order: list[str]) -> str | None:
    working = {r.model for r in results if r.ok}
    return next((m for m in order if m in working), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", action="append",
                        choices=["catalog", "models", "dialects", "speed"])
    parser.add_argument("--models", help="comma-separated ids for the models and speed stages, "
                        "instead of the OpenAI list plus the catalog plus GLM")
    parser.add_argument("--dialect-models", help="comma-separated ids for the dialects stage")
    parser.add_argument("--workers", type=int, default=4,
                        help="parallel calls in the models and speed stages")
    args = parser.parse_args()
    stages = args.stage or ["catalog", "models", "dialects"]

    print(f"# EnMaaS probe, {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, {BASE}\n")
    print("Written by `scripts/enmaas/probe.py`; its `--help` says how to run it again.\n")
    listed = get_catalog() if "catalog" in stages else []
    candidates = args.models.split(",") if args.models else (
        OPENAI + [m for m in listed if m not in OPENAI] + [GLM])
    results: list[Result] = []
    if "models" in stages:
        results += probe_models(candidates, args.workers)
        candidates = [r.model for r in results if r.ok]
    if "dialects" in stages:
        if args.dialect_models:
            chosen = args.dialect_models.split(",")
        else:
            claude = CLAUDE_PICK + [m for m in listed if m.startswith("claude-")]
            chosen = [GLM] + [m for m in (pick(results, OPENAI), pick(results, claude)) if m]
        results += probe_dialects(chosen)
    if results:
        print_rates(results)
        print_tokens(results)
    if "speed" in stages:
        probe_speed(candidates, args.workers)


if __name__ == "__main__":
    main()
