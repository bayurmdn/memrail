"""Generate Claude Code skill + settings files."""
from __future__ import annotations

import json
from pathlib import Path

SKILL_MD = """---
name: memrail
description: Compress long agent context before a model call. Use when history grows large, tool output is bloated, or the user asks to summarize context.
---

# memrail

Use this skill when:
- The current context feels large or approaching limits
- A long agent run has accumulated many tool call results
- You are about to start a new reasoning step but the history is noisy
- The user asks to compress, clean up, or summarize context

## Invoke

```bash
memrail compress --input context.json --max-tokens 80000
```

Or pipe:

```bash
echo "$CONTEXT_JSON" | memrail compress
```

Output is a compressed JSON list of messages safe for the next model call.

## Behavior
- Keep CRITICAL (objectives, errors, system) verbatim
- Keep USEFUL (recent steps) if under budget
- Replace RESTORABLE (large tool output, DOM) with memory pointers
- Summarize or drop DISPOSABLE (stale, redundant)
- Report to stderr
"""

SETTINGS_JSON = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Task",
                "hooks": [
                    {
                        "type": "command",
                        "command": "memrail stats --input /tmp/memrail_context.json || true",
                    }
                ],
            }
        ]
    },
    "permissions": {
        "allow": [
            "Bash(memrail compress:*)",
            "Bash(memrail stats:*)",
            "Bash(memrail restore:*)",
        ]
    },
}


def install(project_root: Path) -> list[Path]:
    project_root = Path(project_root).expanduser().resolve()
    skill_dir = project_root / ".claude" / "skills" / "memrail"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(SKILL_MD)

    settings_path = project_root / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(SETTINGS_JSON, indent=2))

    return [skill_path, settings_path]
