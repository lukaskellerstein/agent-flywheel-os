"""LiteLLM pre-call hook: make a request one a chat-completions engine accepts.

It acts only on the aliases in CHAT_ONLY (GLM 5.3 on EnMaaS and the laptop's
local engine); every other alias, GPT and Claude on EnMaaS, passes untouched,
because they need the Responses and Messages fields this hook removes. It was
written for Cerebras, which the gateway no longer routes (spec 01 section 2,
decision 9); the name stays.

Cerebras speaks chat completions only and validates strictly. Measured on
2026-10-05 with one-token requests (PLAN.md section 2, "Model gateway"):

- `reasoning_effort` must be none, low, medium or high. Codex sends the
  Responses API object `reasoning: {effort, summary}`, and LiteLLM's bridge
  passes it on as an object: 400.
- An assistant message may carry no `thinking_blocks`, `reasoning_content`
  or `thinking` content part. Claude Code sends the thinking block of the
  last reply back on the next turn, and LiteLLM turns it into
  `thinking_blocks`: 400 "property unsupported".
- An unknown top-level field is a 400 too. LiteLLM passes `client_metadata`
  and the Responses API fields on.
- Every system message must come first ("System message must be at the
  beginning"). Claude Code sends its identity as the `system` field and its
  environment block as a system-role message after the user message; Codex
  sends `instructions` and, with `developer_instructions` set, a developer
  item after the user item.

- The token counts of a stream. Cerebras sends the usage of a stream only
  when the request carries `stream_options.include_usage` (LiteLLM's
  Cerebras provider drops the option; litellm.yaml allows it through), and
  it puts the usage on the finish chunk itself, not on a chunk of its own
  as OpenAI does. LiteLLM `main-stable` of 2026-10-05 loses a usage that
  rides on the finish chunk and reports its own tokenizer count instead;
  on the Responses route it has no messages to count, so Codex got 0 input
  tokens on every turn and six tickets cost one cent (measured). The hook
  fills a 0 input count on the Responses route with the same kind of
  estimate from the request, so Codex and Claude Code are counted alike.
  Both are estimates until LiteLLM reads Cerebras's chunk (section 7 of
  PLAN.md has the measured gap: 63 against 54 tokens on a Czech prompt).

The hook runs before the model call on every route, removes the first three,
merges every system text into one system message at the top (on the
Messages route the `system` field and the system-role messages, on the
Responses route `instructions` and the system or developer items), asks for
the usage on every stream, and fills the input count after the call.
Loaded by litellm.yaml (`callbacks: cerebras_hook.proxy_handler_instance`).
"""

from typing import Any

import litellm
from litellm.integrations.custom_logger import CustomLogger

# The alias prefixes of the engines that speak chat completions alone
# (litellm.yaml). A new alias of such an engine gets its prefix here.
CHAT_ONLY = ("enmaas-glm-", "unsloth-")
LEVELS = {"none", "low", "medium", "high"}
DEFAULT_LEVEL = "low"
REASONING_FIELDS = ("thinking_blocks", "reasoning_content", "reasoning")
THINKING_PARTS = ("thinking", "redacted_thinking")
DROP_FIELDS = (
    "client_metadata", "metadata", "store", "prompt_cache_key", "safety_identifier",
    "service_tier", "include", "truncation", "previous_response_id",
)


def level_of(value: Any) -> str | None:
    """A reasoning level from a string or from a Responses-style object."""
    if isinstance(value, dict):
        value = value.get("effort")
    if value is None:
        return None
    return value if value in LEVELS else DEFAULT_LEVEL


def strip_reasoning(messages: Any) -> None:
    """Drop reasoning fields and thinking parts from assistant messages, in place."""
    if not isinstance(messages, list):
        return
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        for field in REASONING_FIELDS:
            message.pop(field, None)
        content = message.get("content")
        if isinstance(content, list):
            kept = [p for p in content if not (isinstance(p, dict) and p.get("type") in THINKING_PARTS)]
            message["content"] = kept if kept else ""


SYSTEM_ROLES = ("system", "developer")


TEXT_PARTS = ("text", "input_text", "output_text")


def texts_of(content: Any) -> list[str]:
    """A message's content as its text pieces (chat or Responses parts);
    anything else is dropped."""
    if isinstance(content, str):
        return [content] if content else []
    if isinstance(content, list):
        return [p["text"] for p in content if isinstance(p, dict) and p.get("type") in TEXT_PARTS and p.get("text")]
    return []


def merge_input_system(data: dict) -> None:
    """The Responses API route: fold every system or developer item of `input`
    into `instructions`, which LiteLLM turns into the first system message.
    Codex puts `developer_instructions` after the user item (measured
    2026-10-05), and Cerebras wants every system message first."""
    items = data.get("input")
    if not isinstance(items, list):
        return
    system_items = [i for i in items if isinstance(i, dict) and i.get("role") in SYSTEM_ROLES]
    if not system_items:
        return
    texts = texts_of(data.get("instructions")) + [t for i in system_items for t in texts_of(i.get("content"))]
    data["instructions"] = "\n\n".join(texts)
    data["input"] = [i for i in items if not (isinstance(i, dict) and i.get("role") in SYSTEM_ROLES)]


def merge_system(messages: Any, system: Any = None) -> Any:
    """One system message, first, as one string: the Anthropic `system` field
    (a string or text blocks), then every system or developer message of the
    list, in their order. Other messages keep their order. Claude Code 2.1
    sends its identity in `system` and its environment block as a system-role
    message after the user message; LiteLLM keeps both where they are, and
    Cerebras wants every system message first. One string, not parts: LiteLLM
    splits a system message with several text parts into several messages
    again (measured 2026-10-05), and a cache marker means nothing to Cerebras.
    A list with at most one system message at index 0 and no `system` field is
    returned as it is."""
    if not isinstance(messages, list):
        return messages
    in_list = [m for m in messages if isinstance(m, dict) and m.get("role") in SYSTEM_ROLES]
    if system is None and (not in_list or (len(in_list) == 1 and messages[0] is in_list[0] and in_list[0].get("role") == "system")):
        return messages
    texts = texts_of(system) + [t for m in in_list for t in texts_of(m.get("content"))]
    rest = [m for m in messages if not (isinstance(m, dict) and m.get("role") in SYSTEM_ROLES)]
    return [{"role": "system", "content": "\n\n".join(texts)}, *rest] if texts else rest


def shape(data: dict) -> dict:
    """The request as Cerebras takes it. Pure, so a test can call it."""
    if "reasoning" in data:
        level = level_of(data.pop("reasoning"))
        if level:
            data["reasoning_effort"] = level
    if "reasoning_effort" in data:
        data["reasoning_effort"] = level_of(data["reasoning_effort"]) or DEFAULT_LEVEL
    strip_reasoning(data.get("messages"))
    strip_reasoning(data.get("input"))
    merge_input_system(data)
    system = data.pop("system", None)
    if "messages" in data or system is not None:
        data["messages"] = merge_system(data.get("messages") or [], system)
    for field in DROP_FIELDS:
        data.pop(field, None)
    if data.get("stream"):
        options = data.get("stream_options") if isinstance(data.get("stream_options"), dict) else {}
        data["stream_options"] = {**options, "include_usage": True}
    return data


def chat_messages_of(data: dict) -> list[dict]:
    """The request's text as chat messages, for a token count: the chat
    route's `messages`, or the Responses route's `instructions`, its input
    items and the outputs of its function calls."""
    if isinstance(data.get("messages"), list):
        return data["messages"]
    messages: list[dict] = []
    if data.get("instructions"):
        messages.append({"role": "system", "content": str(data["instructions"])})
    items = data.get("input")
    if isinstance(items, str):
        return [*messages, {"role": "user", "content": items}]
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("role"):
            messages.append({"role": item["role"], "content": "\n".join(texts_of(item.get("content")))})
        elif item.get("type") == "function_call_output":
            messages.append({"role": "tool", "content": str(item.get("output") or "")})
        elif item.get("type") == "function_call":
            messages.append({"role": "assistant", "content": f"{item.get('name', '')} {item.get('arguments', '')}"})
    return messages


def estimate_input_tokens(data: dict) -> int:
    """LiteLLM's own count of the request, the same count it reports for a
    stream whose provider usage it lost. 0 when it cannot count."""
    try:
        return int(litellm.token_counter(model=str(data.get("model") or ""), messages=chat_messages_of(data)))
    except Exception:
        return 0


def chat_only(data: dict) -> bool:
    """The request names an alias of a chat-completions-only engine."""
    return str(data.get("model") or "").startswith(CHAT_ONLY)


class CerebrasShape(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data: dict, call_type: str):
        return shape(data) if chat_only(data) else data

    async def async_post_call_streaming_iterator_hook(self, user_api_key_dict, response, request_data: dict):
        """The Responses route of a chat-only alias: a `response.completed`
        event with 0 input tokens gets the estimate; every other event passes
        as it is."""
        fill = chat_only(request_data)
        async for event in response:
            if fill and getattr(event, "type", None) == "response.completed":
                usage = getattr(getattr(event, "response", None), "usage", None)
                if usage is not None and not getattr(usage, "input_tokens", 0):
                    estimate = estimate_input_tokens(request_data)
                    if estimate:
                        usage.input_tokens = estimate
                        usage.total_tokens = estimate + int(getattr(usage, "output_tokens", 0) or 0)
            yield event


proxy_handler_instance = CerebrasShape()
