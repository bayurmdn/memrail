# Integrations

## Claude Code

The fastest way to get started with Claude Code.

```bash
memrail init claude
```

This writes two files into your project:

**`.claude/skills/memrail/SKILL.md`** — tells Claude when to invoke memrail (when context grows large, before new reasoning steps, when the user asks to compress).

**`.claude/settings.json`** — hooks + permission allowlist:
- `PreToolUse` hook: runs `memrail stats` before `Task` tool calls so Claude can see token usage
- Allows `memrail compress`, `memrail stats`, `memrail restore` without confirmation prompts

Once installed, Claude Code can call memrail directly from the terminal during long agent sessions.

### Manual trigger

At any point in a session, tell Claude:

> "Run memrail compress on the current context before continuing."

Or use the skill:

```bash
memrail compress --input context.json --max-tokens 80000
```

---

## Python agent loop

The most common integration pattern — wrap your history list before every model call:

```python
from memrail import compress, is_over_budget

class Agent:
    def __init__(self):
        self.history = []

    def step(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        # Compress before the model call
        if is_over_budget(self.history, max_tokens=80_000):
            result = compress(self.history, max_tokens=80_000)
            self.history = result.messages
            print(result.summary)

        response = model_call(self.history)
        self.history.append({"role": "assistant", "content": response})
        return response
```

For always-on compression (regardless of budget):

```python
result = compress(self.history, max_tokens=80_000)
self.history = result.messages
```

---

## CrewAI

Wrap the task callback to compress before each agent handoff:

```python
from crewai import Task, Agent, Crew
from memrail import compress

def compress_context(messages: list[dict]) -> list[dict]:
    return compress(messages, max_tokens=80_000).messages

# Inject into your task execution hook or override the crew's context manager
```

---

## LangChain / LangGraph

Use memrail as a node in your graph that fires before any LLM node:

```python
from langgraph.graph import StateGraph
from memrail import compress

def compress_node(state: dict) -> dict:
    result = compress(state["messages"], max_tokens=80_000)
    return {"messages": result.messages}

builder = StateGraph(...)
builder.add_node("compress", compress_node)
builder.add_edge("compress", "llm")
```

For conditional compression (only when over budget):

```python
from memrail import is_over_budget

def should_compress(state: dict) -> str:
    return "compress" if is_over_budget(state["messages"]) else "llm"

builder.add_conditional_edges("router", should_compress)
```

---

## Custom integration

Any agent framework works as long as you have access to the message list. The minimal integration is three lines:

```python
from memrail import compress

result = compress(your_messages, max_tokens=80_000)
your_messages = result.messages
```

### Persisting the store across runs

If your agent restarts between steps and you want to restore pointers:

```python
from memrail import compress
from memrail.core.store import MemrailStore

store = MemrailStore("~/.memrail/myagent-store.json")
result = compress(messages, store=store)

# Later, to restore an artifact:
content = store.get(pointer_id)
```

### Inspecting what was compressed

```python
result = compress(messages)

print(f"Reduced by {result.ratio:.0%}")
print(f"Pointerized IDs: {result.pointer_ids}")
print(f"Tier breakdown: {result.tier_counts}")
```

### Writing a custom integration module

Follow the pattern in `memrail/integrations/claude_code.py`:

1. Create `memrail/integrations/<framework>.py`
2. Expose an `install(project_root: Path) -> list[Path]` function
3. Wire it into `memrail/cli/main.py` as a subcommand of `init`
4. Add tests in `tests/test_<framework>.py`

---

## Pointer recovery across sessions

Pointers survive as long as the store file exists. To recover an artifact in a new session:

```python
from memrail.core.store import MemrailStore
from memrail.core.pointer import get_pointer_id

store = MemrailStore("~/.memrail/store.json")

# From a pointer token in a message
pointer_token = "[memrail:tool-result:a3f9b2c1d4e5f6a7]"
pid = get_pointer_id(pointer_token)
original = store.get(pid)

# List all stored artifacts
all_ids = store.list_pointers()
```

Or from the CLI:

```bash
memrail restore a3f9b2c1d4e5f6a7
```
