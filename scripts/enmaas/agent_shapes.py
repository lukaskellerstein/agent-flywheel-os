#!/usr/bin/env python3
"""Check the gateway with requests shaped like the agents' and the judge's.

The probe (probe.py) sends one plain request per dialect; the agents send
more. Each request here is a second turn after a tool call, with the fields
its client sends: Claude Code (Messages: system blocks with cache_control,
thinking), Codex (Responses: instructions, a developer item, reasoning with a
summary, include, store, prompt_cache_key), OpenCode (Chat: tool messages,
reasoning_effort, temperature, stream usage). The judge is the harness's own
shape, a forced tool call on Chat Completions (agent-eval-harness
skills/eval-run/scripts/score.py, _openai_judge_request); judge-json asks for
JSON mode instead. Every answer should say 12 C and light rain, or grade 1.

It runs in the gateway's pod, against http://localhost:4000, with
client=alias pairs. A few cents a run:

    oc exec -i -n agent-flywheel deploy/gateway -- python3 - \
        claude-code=enmaas-gpt-5-mini codex=enmaas-gpt-5-mini opencode=enmaas-gpt-5-mini \
        opencode=enmaas-gpt-6-luna judge=enmaas-gpt-6-sol < scripts/enmaas/agent_shapes.py
"""

import json
import sys
import time
import urllib.error
import urllib.request

GATEWAY = "http://localhost:4000/v1"
TOOL = {"name": "get_weather", "description": "The current weather in a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
ASK = "What is the weather in Brno? Use the tool, then answer in one sentence."
RESULT = "12 C, light rain"


def claude_code(model):
    return "/messages", {
        "model": model, "max_tokens": 4096, "stream": True,
        "system": [{"type": "text", "text": "You are a coding agent.", "cache_control": {"type": "ephemeral"}}],
        "thinking": {"type": "enabled", "budget_tokens": 1024},
        "tools": [{"name": TOOL["name"], "description": TOOL["description"], "input_schema": TOOL["parameters"]}],
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": ASK}]},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {"city": "Brno"}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": RESULT}]},
        ],
    }


def codex(model):
    return "/responses", {
        "model": model, "stream": True, "store": False, "parallel_tool_calls": False,
        "instructions": "You are a coding agent.",
        "reasoning": {"effort": "low", "summary": "auto"},
        "include": ["reasoning.encrypted_content"], "prompt_cache_key": "probe-1",
        "tools": [{"type": "function", "strict": False, **TOOL}],
        "input": [
            {"role": "developer", "content": [{"type": "input_text", "text": "Be brief."}]},
            {"role": "user", "content": [{"type": "input_text", "text": ASK}]},
            {"type": "function_call", "call_id": "call_1", "name": "get_weather", "arguments": json.dumps({"city": "Brno"})},
            {"type": "function_call_output", "call_id": "call_1", "output": RESULT},
        ],
    }


def opencode(model):
    return "/chat/completions", {
        "model": model, "stream": True, "stream_options": {"include_usage": True},
        "max_tokens": 4096, "temperature": 0, "reasoning_effort": "low",
        "tools": [{"type": "function", "function": TOOL}],
        "messages": [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": ASK},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "get_weather", "arguments": json.dumps({"city": "Brno"})}}]},
            {"role": "tool", "tool_call_id": "call_1", "content": RESULT},
        ],
    }


def judge(model):
    return "/chat/completions", {
        "model": model, "temperature": 0, "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": 'Grade the answer. Reply with JSON: {"score": 0 or 1, "reason": "..."}.'},
            {"role": "user", "content": "Question: What is 2 + 2?\nAnswer: 4"},
        ],
    }


def judge_tool(model):
    """The harness's judge: a forced tool call on Chat Completions
    (skills/eval-run/scripts/score.py, _openai_judge_request)."""
    grade = {"type": "function", "function": {
        "name": "grade", "description": "Record the grade.",
        "parameters": {"type": "object", "properties": {
            "score": {"type": "integer"}, "reason": {"type": "string"}}, "required": ["score", "reason"]}}}
    return "/chat/completions", {
        "model": model, "max_completion_tokens": 1024, "tools": [grade],
        "tool_choice": {"type": "function", "function": {"name": "grade"}},
        "messages": [
            {"role": "system", "content": "Grade the answer: score 1 if correct, else 0."},
            {"role": "user", "content": "Question: What is 2 + 2?\nAnswer: 4"},
        ],
    }


def send(path, body):
    request = urllib.request.Request(GATEWAY + path, data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json", "x-api-key": "none",
                                              "anthropic-version": "2023-06-01"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            text = response.read().decode("utf-8", "replace")
            return response.status, text, time.monotonic() - start
    except urllib.error.HTTPError as err:
        return err.code, " ".join(err.read().decode("utf-8", "replace").split())[:300], time.monotonic() - start


def answer_of(text):
    """The answer's text, from a stream or a plain JSON body."""
    if not text.lstrip().startswith(("data:", "event:")):
        message = json.loads(text)["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        return " ".join(c["function"]["arguments"] for c in calls) or message.get("content") or ""
    parts = []
    for line in text.splitlines():
        if not line.startswith("data:") or line[5:].strip() == "[DONE]":
            continue
        try:
            event = json.loads(line[5:])
        except ValueError:
            continue
        delta = ((event.get("choices") or [{}])[0] or {}).get("delta") or {}
        parts.append(delta.get("content") or "")
        if event.get("type") == "response.output_text.delta":
            parts.append(event.get("delta", ""))
        if event.get("type") == "content_block_delta" and event.get("delta", {}).get("type") == "text_delta":
            parts.append(event["delta"].get("text", ""))
    return "".join(parts)


CLIENTS = {"claude-code": claude_code, "codex": codex, "opencode": opencode, "judge-json": judge,
           "judge": judge_tool}

print("| client | alias | status | s | answer |")
print("|:--|:--|:--|:--|:--|")
for pair in sys.argv[1:]:
    client, model = pair.split("=")
    status, text, seconds = send(*CLIENTS[client](model))
    shown = " ".join(answer_of(text).split())[:90] if status == 200 else text
    print(f"| {client} | {model} | {status} | {seconds:.1f} | {shown} |")
