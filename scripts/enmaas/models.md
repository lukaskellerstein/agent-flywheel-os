# EnMaaS probe, 2026-10-14 15:24 UTC, https://api.enmaas.devshift.net/v1

Written by `scripts/enmaas/probe.py`; its `--help` says how to run it again.

## Catalog: GET /v1/models

- Authorization: Bearer: 15 ids: gemini-3.6-flash, gemini-3.7-flash, gemini-3.8-flash, gemini-3.1-pro-preview, claude-sonnet-4-5, claude-sonnet-5, claude-haiku-4-5, claude-opus-4-5, claude-opus-4-6, claude-sonnet-4-6, claude-opus-4-7, claude-opus-4-8, claude-opus-5, claude-opus-5-5, claude-sonnet-5-5
- x-api-key: 11 ids: claude-sonnet-4-5, claude-sonnet-5, claude-haiku-4-5, claude-opus-4-5, claude-opus-4-6, claude-sonnet-4-6, claude-opus-4-7, claude-opus-4-8, claude-opus-5, claude-opus-5-5, claude-sonnet-5-5

## Speed and price: 3 streamed answers each, about 300 words

Each id is called from where this probe runs, in its own dialect (Responses for
OpenAI, Messages for Claude, Chat Completions for the rest), at the lowest
reasoning level it takes. *First token*: seconds to the first streamed token,
text or reasoning. *Tokens/s*: the tokens the stream showed, over the time from
the first token to the end; OpenAI's hidden reasoning tokens are left out. The
median of the answers, and the slowest and fastest of them. *Price*: USD per
million tokens, LiteLLM's list price; EnMaaS shows none, and only GLM 5.3 is
free. Models run 4 at a time, so the numbers include EnMaaS under that load.
`gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `o3` and `o4-mini` were measured again at
15:28 UTC: the first run sent them a reasoning level they refuse. The GPT-6 ids,
`gpt-5.6-luna`, `gpt-4.1-nano`, `o3-mini` and `o1` were added at 15:47 UTC.
*(cut)*: an answer hit the limit of 2048 output tokens.

| model | family | dialect | reasoning level | first token s | tokens/s | slowest-fastest | answer s | out tokens | of them reasoning | USD/M in | USD/M out |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| o3-mini | openai | responses | low | 1.06 | 201 | 197-205 | 2.8 | 349 | 0 | 1.1 | 4.4 |
| gemini-3.6-flash | gemini | chat | low | 3.93 | 199 | 185-250 | 5.6 | 1030 | 687 | 0.75 | 3.75 |
| gpt-5-mini | openai | responses | minimal | 0.77 | 171 | 168-180 | 3.0 | 378 | 0 | 0.25 | 2 |
| gpt-4.1-mini | openai | responses | - | 1.00 | 151 | 150-155 | 3.3 | 359 | 0 | 0.4 | 1.6 |
| gpt-5.4-mini | openai | responses | none | 0.65 | 138 | 130-153 | 3.4 | 361 | 0 | 0.75 | 4.5 |
| o4-mini | openai | responses | low | 1.68 | 129 | 123-130 | 4.8 | 466 | 64 | 1.1 | 4.4 |
| gpt-5.4-nano | openai | responses | none | 0.61 | 118 | 103-135 | 3.5 | 346 | 0 | 0.2 | 1.25 |
| gemini-3.7-flash | gemini | chat | low | 7.85 | 118 | 113-150 | 10.8 | 1031 | 680 | 0.75 | 3.75 |
| gpt-4.1-nano | openai | responses | - | 1.04 | 115 | 72-126 | 4.1 | 358 | 0 | 0.1 | 0.4 |
| gpt-6-luna | openai | responses | none | 0.96 | 113 | 111-114 | 4.4 | 398 | 0 | ? | ? |
| claude-sonnet-5-5 | anthropic | messages | - | 1.13 | 107 | 102-116 | 6.7 | 625 | 0 | ? | ? |
| o1 | openai | responses | low | 4.13 | 105 | 98-128 | 7.8 | 754 | 384 | 15 | 60 |
| claude-opus-5-5 | anthropic | messages | - | 1.42 | 104 | 101-105 | 8.0 | 674 | 0 | ? | ? |
| gemini-3.1-pro-preview | gemini | chat | low | 10.44 | 101 | 93-152 | 14.3 | 1059 | 697 | 2 | 12 |
| gemini-3.8-flash | gemini | chat | low | 1.36 | 100 | 90-100 | 5.0 | 365 | 0 | ? | ? |
| gpt-4o | openai | responses | - | 0.97 | 97 | 88-103 | 4.6 | 352 | 0 | 2.5 | 10 |
| gpt-4.1 | openai | responses | - | 0.71 | 94 | 75-98 | 4.6 | 368 | 0 | 2 | 8 |
| gpt-5-nano | openai | responses | minimal | 0.76 | 92 | 90-93 | 5.4 | 424 | 0 | 0.05 | 0.4 |
| gpt-5.6-luna | openai | responses | none | 1.32 | 91 | 85-94 | 5.3 | 372 | 0 | 0.2 | 1.2 |
| gpt-5.1 | openai | responses | none | 0.84 | 89 | 87-90 | 5.1 | 378 | 0 | 1.25 | 10 |
| gpt-4o-mini | openai | responses | - | 1.13 | 86 | 84-103 | 4.7 | 325 | 0 | 0.15 | 0.6 |
| o3 | openai | responses | low | 1.76 | 85 | 67-97 | 6.6 | 442 | 0 | 2 | 8 |
| claude-opus-5 | anthropic | messages | - | 3.04 | 79 | 73-79 | 13.1 | 777 | 0 | 5 | 25 |
| claude-haiku-4-5 | anthropic | messages | - | 0.59 | 79 | 77-81 | 5.4 | 390 | 0 | 1 | 5 |
| claude-sonnet-5 | anthropic | messages | - | 0.78 | 76 | 61-87 | 9.2 | 572 | 0 | 2 | 10 |
| rits/zai-org/glm-5-3 | rits | chat | - | 1.10 | 76 | 76-82 | 26.0 | 2048 (cut) | 1742 | 0 | 0 |
| claude-opus-4-8 | anthropic | messages | - | 0.77 | 67 | 64-69 | 9.8 | 595 | 0 | 5 | 25 |
| gpt-5 | openai | responses | minimal | 0.80 | 62 | 54-66 | 7.5 | 413 | 0 | 1.25 | 10 |
| gpt-5.6 | openai | responses | none | 1.16 | 58 | 52-58 | 8.0 | 392 | 0 | 4 | 20 |
| gpt-6-sol | openai | responses | none | 0.87 | 58 | 51-58 | 6.8 | 345 | 0 | ? | ? |
| gpt-5.3-codex | openai | responses | none | 0.81 | 49 | 49-55 | 7.7 | 350 | 0 | 1.75 | 14 |
| gpt-5.2 | openai | responses | none | 0.82 | 48 | 47-48 | 8.9 | 388 | 0 | 1.75 | 14 |
| gpt-5.4 | openai | responses | none | 1.11 | 48 | 46-48 | 8.8 | 361 | 0 | 2.5 | 15 |
| gpt-5.5 | openai | responses | none | 0.97 | 41 | 38-43 | 10.1 | 377 | 0 | 5 | 30 |
| gpt-6-astra | openai | responses | low | 1.64 | 40 | 40-42 | 10.4 | 359 | 0 | ? | ? |
| claude-sonnet-4-6 | anthropic | messages | - | 1.07 | 37 | 37-41 | 10.8 | 374 | 0 | 3 | 15 |
| claude-opus-4-6 | anthropic | messages | - | 1.58 | 36 | 33-38 | 13.1 | 415 | 0 | 5 | 25 |
| gpt-6.1-sol | openai | responses | low | 2.00 | 34 | 32-41 | 12.2 | 376 | 19 | ? | ? |

Not on EnMaaS for this key (404 or 403): gpt-5.6-mini, gpt-5.6-nano, gpt-5.6-codex, gpt-5.5-mini, gpt-5.5-nano, gpt-5.5-codex, gpt-5.2-codex, gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5-codex, gpt-oss-120b, gpt-oss-20b, claude-sonnet-4-5, claude-opus-4-5, claude-opus-4-7.

This stage spent about 0.56 USD at list price, plus the tokens of 7 models with no price in the table: gemini-3.8-flash, claude-opus-5-5, claude-sonnet-5-5, gpt-6.1-sol, gpt-6-sol, gpt-6-astra, gpt-6-luna.


## GPT-6 and the other ids no list shows

OpenAI's newest models answer only under a code name: `gpt-6-sol`,
`gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` and `gpt-5.6-luna`, and `gpt-5.6`
is served as `gpt-5.6-sol`. Plain `gpt-6` is a 404, and so are `gpt-6-mini`,
`gpt-6-nano`, `gpt-6-pro`, `gpt-6-codex`, `gpt-6.5-sol`, `gpt-7-sol` and
about 40 more guessed names (2026-10-14). EnMaaS's catalog lists no OpenAI
model, so a guess is the only test, and this list can miss a name.

`gpt-6.1-sol` and `gpt-6-astra` take no reasoning level below `low`, so they
take tools only on Responses; `gpt-6-sol` and `gpt-6-luna` take tools on Chat
Completions with `reasoning_effort: "none"`. LiteLLM's table of 2026-09-02 has
no GPT-6 price; `gpt-5.6-luna` is 0.2 and 1.2 USD per million tokens.

The `-pro` models exist but are not measured: they refuse a low reasoning
level, and their list prices in and out per million tokens are `gpt-5.5-pro`
30 and 180, `gpt-5.4-pro` 30 and 180, `gpt-5.2-pro` 21 and 168, `gpt-5-pro` 15
and 120, `o3-pro` 20 and 80, `o1-pro` 150 and 600.
