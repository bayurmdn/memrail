# Configuration

memrail has no config file — everything is passed via arguments or the Python API. This keeps it stateless and easy to reason about.

---

## Token budget

### CLI

```bash
memrail compress --max-tokens 80000
```

### Python

```python
from memrail import compress

result = compress(messages, max_tokens=80_000)
```

**Default:** `80_000`

**Choosing a value:** Set this to ~80% of the model's context window. For Claude models:

| Model | Context window | Recommended `max_tokens` |
|-------|---------------|--------------------------|
| Claude Haiku 4.5 | 200k | `160_000` |
| Claude Sonnet 4.6 | 200k | `160_000` |
| Claude Opus 4.7 | 200k | `160_000` |
| GPT-4o | 128k | `100_000` |

Leave headroom for the model's output tokens. A buffer of 20% is a safe default.

---

## Pointer store

The store persists pointerized artifacts so they can be recovered with `memrail restore`.

### CLI

```bash
memrail compress --store ~/.memrail/store.json
memrail restore <id> --store ~/.memrail/store.json
```

### Python

```python
from memrail.core.store import MemrailStore
from memrail import compress

store = MemrailStore("~/.memrail/store.json")  # persisted
result = compress(messages, store=store)
```

**Default:** `~/.memrail/store.json`

**In-memory (no persistence):**

```python
store = MemrailStore()  # no path — ephemeral
```

In-memory stores are useful for testing or for agents that don't need artifact recovery across runs.

**Per-project stores** — isolate artifacts by project to avoid cross-contamination:

```bash
memrail compress --input ctx.json --store ./.memrail/store.json
```

---

## Classifier thresholds

The classifier has two tunable constants in `memrail/core/classifier.py`. These are not exposed via CLI — change them in code if you need different sensitivity.

```python
RECENT_WINDOW = 5          # messages from the tail counted as USEFUL
LARGE_CONTENT_CHARS = 2000 # content longer than this triggers RESTORABLE
```

**When to adjust:**

- Increase `RECENT_WINDOW` if your agent makes many small steps and you want more recent context preserved.
- Decrease `LARGE_CONTENT_CHARS` if you want even moderate-size messages pointerized (more aggressive compression).
- Increase `LARGE_CONTENT_CHARS` if you find useful tool outputs are being pointerized too eagerly.

---

## LLM summarization

By default, DISPOSABLE messages are replaced with a static placeholder. Enable real summarization by passing an `LLMClient`:

```python
from memrail import compress

class MySummarizer:
    def summarize(self, text: str, max_tokens: int = 200) -> str:
        # call any LLM here
        return your_llm.complete(f"Summarize:\n{text}")

result = compress(messages, llm_client=MySummarizer())
```

The `LLMClient` protocol:

```python
class LLMClient(Protocol):
    def summarize(self, text: str, max_tokens: int = 200) -> str: ...
```

Any object with a `summarize` method works. No base class required.

**Anthropic built-in** (install `memrail[anthropic]`):

```python
from anthropic import Anthropic

class AnthropicSummarizer:
    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self.client = Anthropic()
        self.model = model

    def summarize(self, text: str, max_tokens: int = 200) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": f"Summarize this agent history in 2-3 sentences, keeping key decisions and errors:\n\n{text}"
            }],
        )
        return resp.content[0].text
```

Use `claude-haiku-4-5-20251001` for summarization — it's fast and cheap and you don't need the full power of Sonnet or Opus for this task.

---

## Claude Code integration settings

`memrail init claude` writes `.claude/settings.json` with this structure:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "memrail stats --input /tmp/memrail_context.json || true"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(memrail compress:*)",
      "Bash(memrail stats:*)",
      "Bash(memrail restore:*)"
    ]
  }
}
```

You can extend the `matcher` to trigger on other tool names, or add a `PostToolUse` hook to auto-compress after heavy tool calls:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "memrail stats || true"
          }
        ]
      }
    ]
  }
}
```
