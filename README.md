# memrail

> A context budget manager for long-running AI agents.

Long-running agents silently degrade when their context grows too large. **memrail** sits between your agent and its history, classifies each message by priority, summarizes stale content, and replaces large artifacts with restorable memory pointers — before every model call.

## Install

```bash
pip install memrail            # core
pip install "memrail[anthropic]"  # optional: LLM-based summarization
```

## Quick start

```python
from memrail import compress

messages = [...]  # your agent history
result = compress(messages, max_tokens=80_000)

print(result.summary)        # "kept=12 pointerized=3 summarized=20 ..."
print(result.tokens_before, "→", result.tokens_after)
next_call_messages = result.messages
```

## How it works

Every message is bucketed into one of four tiers:

| Tier | Definition | Action |
|------|------------|--------|
| CRITICAL | Task objectives, active errors, system prompt | Keep verbatim |
| USEFUL | Recent decisions, last ~5 steps | Keep if under budget |
| RESTORABLE | Large tool output, DOM snapshots, JSON blobs | Replace with `[memrail:...]` pointer |
| DISPOSABLE | Old tangents, redundant chatter | Summarize or drop |

Pointerized artifacts stay in a local store and can be recovered later with `memrail restore <id>`.

## CLI

```bash
memrail compress --input context.json --max-tokens 80000
memrail stats    --input context.json
memrail restore  <pointer-id>
memrail init claude     # scaffold .claude/skills/memrail + settings.json
```

All commands accept stdin:

```bash
cat context.json | memrail compress > compressed.json
```

## Claude Code integration

```bash
memrail init claude
```

Writes `.claude/skills/memrail/SKILL.md` so Claude knows when to invoke the tool, plus a sample `.claude/settings.json` with a `PreToolUse` hook that runs `memrail stats` before heavy tasks.

## Configuration

- `--max-tokens` — default `80_000`.
- `--store` — pointer store path, default `~/.memrail/store.json`.

## Roadmap

- Real tokenizer (tiktoken / anthropic.count_tokens) in place of char-based estimate
- LangGraph middleware adapter
- Browser-agent DOM compression example
- Vector-backed pointer store

## Benchmarking

Memrail includes a benchmark suite to evaluate compression quality across three workload types: coding, browser, and research agents.

```bash
cd benchmarks
python runner.py          # Run baseline + Memrail on all tasks
python report.py          # Generate markdown report and CSV summary
```

Results:

- `baseline_results.json` — token usage, task success, state retention (no compression)
- `memrail_results.json` — same metrics with Memrail enabled
- `REPORT.md` — side-by-side comparison
- `summary.csv` — per-task results

To add tasks, create JSON files in `benchmarks/tasks/{coding,browser,research}/`. See `task_001.json` for the schema.

## Contributing

PRs welcome. Run `pytest` before submitting.
