# Architecture

memrail is a thin pipeline that sits between your agent loop and the model call. It never mutates your original data — it returns a new, compressed message list.

## Overview

```
your agent loop
      │
      │  messages = history.get_all()
      ▼
┌─────────────────────────────────────────────────────┐
│                      compress()                     │
│                                                     │
│  1. classify_all(messages)                          │
│        │                                            │
│        ▼                                            │
│  ┌───────────┐   ┌─────────┐   ┌───────────────┐  │
│  │ CRITICAL  │   │ USEFUL  │   │  RESTORABLE   │  │
│  │ keep as-is│   │ keep if │   │  pointerize   │  │
│  │           │   │ in budget│  │  → store      │  │
│  └───────────┘   └─────────┘   └───────────────┘  │
│                                                     │
│  ┌────────────┐                                     │
│  │ DISPOSABLE │ → summarize group → system message  │
│  └────────────┘                                     │
│                                                     │
│  2. if still over budget → drop_oldest_useful()     │
│                                                     │
│  3. return CompressedContext                        │
└─────────────────────────────────────────────────────┘
      │
      │  model_call(result.messages)
      ▼
   model response
```

## Module map

```
memrail/
├── core/
│   ├── budget.py       token counting + budget checks
│   ├── classifier.py   assign Tier to each message
│   ├── compressor.py   orchestrate compress(), return CompressedContext
│   ├── pointer.py      create/parse [memrail:label:uuid] tokens
│   └── store.py        MemrailStore — in-memory + optional JSON file
├── cli/
│   └── main.py         typer app — compress, stats, restore, init
├── integrations/
│   └── claude_code.py  write SKILL.md + settings.json into .claude/
└── utils/
    └── tokenizer.py    char-based token approximation
```

**Rule:** `core/` modules are pure — no I/O, no subprocess calls. Only `cli/` and `integrations/` touch the filesystem. `compressor.py` is the one exception: it may call an optional `LLMClient` for summarization.

---

## Classifier

`memrail/core/classifier.py`

Each message is assigned one of four tiers via `classify(message, position, total)`:

| Tier | Priority | Signal |
|------|----------|--------|
| `CRITICAL` (1) | Highest | `role == "system"` OR text contains error/exception/traceback/objective/task keywords |
| `USEFUL` (2) | High | Within the last `RECENT_WINDOW` (5) messages |
| `RESTORABLE` (3) | Medium | Content length > `LARGE_CONTENT_CHARS` (2000 chars), especially tool output or HTML |
| `DISPOSABLE` (4) | Lowest | Everything else |

Classification is purely positional and keyword-based — no LLM required.

**Key constants** (in `classifier.py`):

```python
RECENT_WINDOW = 5          # how many trailing messages are "recent"
LARGE_CONTENT_CHARS = 2000 # threshold to trigger RESTORABLE
```

### Classification flow

```
message
  │
  ├─ role == "system"?           → CRITICAL
  ├─ contains CRITICAL_SIGNALS?  → CRITICAL
  ├─ len(text) > 2000?
  │     └─ contains RESTORABLE_SIGNALS or role == "tool"?  → RESTORABLE
  ├─ position >= total - 5?      → USEFUL
  └─ else                        → DISPOSABLE
```

---

## Compressor

`memrail/core/compressor.py`

`compress()` takes the classified list and applies three operations:

### 1. Pointerize (RESTORABLE)

Large artifacts are replaced with a short `[memrail:label:uuid]` token. The original content is saved to `MemrailStore`. The message stays in the list at its original position — only the content changes.

```
original: {"role": "tool", "content": "<html>...8000 chars..."}
replaced: {"role": "tool", "content": "[memrail:tool-result:a3f9...] [8000 chars; preview: <html>...]"}
```

### 2. Summarize (DISPOSABLE)

All DISPOSABLE messages are collected into a single group and replaced with one summary `system` message, prepended to the kept list.

Without an `LLMClient`:
```
[memrail:summary] Dropped 12 stale messages (~4800 chars).
```

With an `LLMClient` (requires `pip install "memrail[anthropic]"`):
```
The agent explored auth routes, attempted fix #1 (failed), retried with patch approach.
```

### 3. Drop oldest USEFUL (budget overflow)

If the resulting list is still over `max_tokens`, the oldest non-system messages are dropped one by one until the budget is met. CRITICAL messages (role=`system`) are always skipped.

### Return value: `CompressedContext`

```python
@dataclass
class CompressedContext:
    messages: list[dict]      # ready to pass to the model
    summary: str              # human-readable one-liner
    tokens_before: int
    tokens_after: int
    tier_counts: dict[Tier, int]
    pointer_ids: list[str]    # IDs of all pointerized artifacts

    @property
    def ratio(self) -> float: ...  # 0.40 = 40% reduction
```

---

## Pointer store

`memrail/core/store.py`

`MemrailStore` is a simple key→value store. Keys are the UUID portion of pointer tokens. Values are the original message dicts.

```python
store = MemrailStore()                           # in-memory only
store = MemrailStore("~/.memrail/store.json")    # persisted to disk
```

On disk the store is a plain JSON file — human-readable, easy to inspect or back up.

```json
{
  "a3f9b2c1...": {
    "role": "tool",
    "content": "<html>original dom snapshot...</html>"
  }
}
```

**Persistence is opt-in.** The CLI defaults to `~/.memrail/store.json`. The Python API defaults to in-memory (pointers are ephemeral per process unless you pass a path).

---

## Token counting

`memrail/utils/tokenizer.py`

The current tokenizer uses a character-based approximation: `tokens ≈ len(text) / 4`. This is fast and dependency-free but approximate (+/- 15% for typical English text).

Each message also gets a fixed overhead of `+4` tokens to account for the role prefix and message framing that real tokenizers include.

**Roadmap:** Replace with `tiktoken` or `anthropic.count_tokens` for exact counts. This is the highest-priority item in the roadmap — it's a drop-in swap in `tokenizer.py`.

---

## LLM-based summarization

By default, DISPOSABLE messages are summarized with a static placeholder. To enable real LLM summarization, install the anthropic extra and pass an `LLMClient`:

```python
from anthropic import Anthropic

class AnthropicSummarizer:
    def __init__(self):
        self.client = Anthropic()

    def summarize(self, text: str, max_tokens: int = 200) -> str:
        msg = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": f"Summarize this agent history in 2-3 sentences:\n\n{text}"}],
        )
        return msg.content[0].text

result = compress(messages, llm_client=AnthropicSummarizer())
```

The `LLMClient` protocol requires only one method: `summarize(text: str, max_tokens: int) -> str`. Any provider works.

---

## Data flow example

```
Input: 25 messages, 120,000 tokens
  ├─  2 CRITICAL  →  kept verbatim         (8,000 tokens)
  ├─  5 USEFUL    →  kept verbatim         (12,000 tokens)
  ├─  3 RESTORABLE → pointerized           (≈300 tokens after, originals in store)
  └─ 15 DISPOSABLE → 1 summary message     (≈200 tokens)

Output: 11 messages, ~20,500 tokens  →  83% reduction
```
