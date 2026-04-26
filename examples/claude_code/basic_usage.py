"""Basic memrail usage with a Claude Code-style agent loop."""
from memrail import compress

# Simulate a long-running agent history
messages = [
    {"role": "system", "content": "You are a coding assistant. Task: refactor the auth module."},
    {"role": "user", "content": "Start by reviewing the existing code."},
    {"role": "assistant", "content": "I'll review the auth module now."},
    # ... many more turns accumulate over time ...
    {
        "role": "tool",
        "content": "<html>" + "x" * 3000 + "</html>",  # large DOM snapshot
    },
    {"role": "assistant", "content": "Found 3 issues in the auth module. Working on fix #1."},
    {"role": "assistant", "content": "Fix #1 complete. Moving to fix #2."},
    {"role": "assistant", "content": "Fix #2 complete. Moving to fix #3."},
    {"role": "user", "content": "Also make sure error messages are user-friendly."},
    {"role": "assistant", "content": "Noted. Will update error messages in fix #3."},
]

# Compress before the next model call
result = compress(messages, max_tokens=80_000)

print(result.summary)
# Example: kept=6  pointerized=1  summarized=2  tokens: 4800 → 2100

# Use the compressed messages for the next API call
next_messages = result.messages

# Restore a pointer if needed later
from memrail.core.store import MemrailStore

store = MemrailStore()
for msg in next_messages:
    content = msg.get("content", "")
    if isinstance(content, str) and content.startswith("[memrail:"):
        pointer_id = content.split(":")[1].rstrip("]")
        original = store.get(pointer_id)
        print(f"Restored {len(original)} chars for pointer {pointer_id}")
