# memrail skill

memrail is a context budget manager. Use it to keep long agent sessions healthy.

## When to invoke

- Before any tool call that will add large output to context (bash, file reads, web fetch)
- When the conversation is long and you feel context may be bloating
- Whenever the user asks about context size or token usage
- At the start of a new sub-task within a long session

## Commands

```bash
# Check current token usage by tier
memrail stats --input context.json

# Compress and return a leaner context
memrail compress --input context.json --max-tokens 80000

# Restore a pointerized artifact
memrail restore <pointer-id>
```

## Tiers

| Tier | What it means |
|------|--------------|
| CRITICAL | Never drop — system prompts, active errors, task goals |
| USEFUL | Keep while under budget — recent decisions |
| RESTORABLE | Replaced with a pointer — large tool output, snapshots |
| DISPOSABLE | Summarized or dropped — old tangents |

## Key rule

Run `memrail stats` BEFORE a heavy tool call. If tokens are above 70% of budget, run `memrail compress` first.
