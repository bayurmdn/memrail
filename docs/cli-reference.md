# CLI Reference

## Installation

```bash
pip install memrail
memrail --help
```

---

## Commands

### `memrail compress`

Compress a message list. Reads JSON, writes compressed JSON.

```bash
memrail compress [OPTIONS]
```

**Options**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--input PATH` | `-i` | stdin | JSON file containing the message array |
| `--output PATH` | `-o` | stdout | Write compressed messages here |
| `--max-tokens INT` | `-m` | `80000` | Hard token budget |
| `--store PATH` | | `~/.memrail/store.json` | Where to persist pointerized artifacts |

**Examples**

```bash
# From file → stdout
memrail compress --input context.json

# From file → file
memrail compress --input context.json --output compressed.json

# From stdin → stdout (pipeline)
cat context.json | memrail compress > compressed.json

# Custom token budget
memrail compress --input context.json --max-tokens 40000

# Custom store location
memrail compress --input context.json --store /tmp/myproject-store.json
```

**Output**

- `stdout` — compressed JSON array (same shape as input)
- `stderr` — one-line summary with tier counts and ratio:

```
memrail: kept=7 pointerized=2 summarized=15 4800→2100 tokens (ratio=56.3%)
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Invalid JSON or input not a list |

---

### `memrail stats`

Inspect token usage and tier breakdown without modifying anything.

```bash
memrail stats [OPTIONS]
```

**Options**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--input PATH` | `-i` | stdin | JSON file with messages |
| `--max-tokens INT` | `-m` | `80000` | Budget to compare against |

**Examples**

```bash
memrail stats --input context.json
memrail stats --input context.json --max-tokens 40000
cat context.json | memrail stats
```

**Output** (rich table to stdout)

```
         memrail stats
┌────────────┬───────┬────────┐
│ Tier       │ Count │ Tokens │
├────────────┼───────┼────────┤
│ CRITICAL   │     2 │   1200 │
│ USEFUL     │     5 │   3100 │
│ RESTORABLE │     3 │   8400 │
│ DISPOSABLE │    15 │  11300 │
│ TOTAL      │    25 │  24000 │
│ budget     │     - │ 24000/80000 │
└────────────┴───────┴────────┘
```

---

### `memrail restore`

Retrieve the original content of a pointerized artifact.

```bash
memrail restore [OPTIONS] POINTER_ID
```

**Arguments**

| Arg | Description |
|-----|-------------|
| `POINTER_ID` | The UUID or the full `[memrail:label:uuid]` string |

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--store PATH` | `~/.memrail/store.json` | Store to read from |

**Examples**

```bash
# Restore by UUID
memrail restore a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5

# Restore by full pointer string (quotes required)
memrail restore "[memrail:tool-result:a3f9b2c1d4e5f6a7]"

# Pipe into jq
memrail restore a3f9b2c1 | jq '.content'

# From a custom store
memrail restore a3f9b2c1 --store /tmp/myproject-store.json
```

**Output** — original message dict as JSON on stdout:

```json
{
  "role": "tool",
  "content": "<html>... original 8000-char DOM snapshot ...</html>"
}
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | Found and printed |
| `1` | Pointer not found in store |

---

### `memrail init claude`

Scaffold memrail into a Claude Code project.

```bash
memrail init claude [OPTIONS]
```

**Options**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--project PATH` | `-p` | current dir | Root of the Claude Code project |

**Examples**

```bash
# Install into the current project
memrail init claude

# Install into a specific project
memrail init claude --project ~/dev/myagent
```

**Files written**

| File | Purpose |
|------|---------|
| `.claude/skills/memrail/SKILL.md` | Skill description — tells Claude when and how to call memrail |
| `.claude/settings.json` | `PreToolUse` hook that runs `memrail stats` before `Task` tool calls + permission allowlist |

Both files are **overwritten** if they already exist.

---

## Stdin/stdout pipeline patterns

memrail is pipe-friendly. All commands read from stdin when `--input` is not given and write to stdout by default.

```bash
# Check stats before compressing
cat context.json | memrail stats
cat context.json | memrail compress | jq length

# In-place compress (using temp file)
memrail compress --input context.json --output context.json.tmp \
  && mv context.json.tmp context.json

# Chain with your agent runner
python run_agent.py --dump-context /tmp/ctx.json
memrail compress --input /tmp/ctx.json --output /tmp/ctx_compressed.json
python run_agent.py --load-context /tmp/ctx_compressed.json
```
