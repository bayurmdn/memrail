# CLAUDE.md

## Project Overview
Memrail is a context budget manager for long-running AI agents.
It compresses, summarizes, and pointerizes agent history before each model call.

## Code Style
- Python 3.10+
- Use type hints everywhere
- Follow PEP 8
- No magic numbers — define all thresholds as named constants
- Prefer pure functions in core/ modules; side effects only in cli/ and integrations/

## Key Invariants
- Memrail must NEVER discard content marked as CRITICAL priority
- Summarization must be task-aware, not blind truncation
- Memory pointers must be restorable — every artifact stored must be retrievable
- Token budget check must run BEFORE every model call, not after

## File Boundaries
- core/ = pure logic, no I/O, no LLM calls except compressor.py
- cli/ = user-facing commands only
- integrations/ = third-party adapter code only
- utils/ = stateless helpers only

## Testing
- Every core/ function must have a corresponding test in tests/
- Tests must not make real LLM API calls — use mocks
