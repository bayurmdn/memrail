"""Generate state retention probe questions for benchmark tasks."""

from typing import Any


def coding_probes(task: dict[str, Any], context: list[dict]) -> list[dict]:
    """Generate probe questions for coding tasks."""
    return [
        {
            "question": "What function was changed most recently?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "Which test failed before the last edit?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "What requirement is still unmet?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "Which file path is the main target?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "What was the last successful edit?",
            "type": "reasoning",
            "importance": "high"
        },
    ]


def browser_probes(task: dict[str, Any], context: list[dict]) -> list[dict]:
    """Generate probe questions for browser tasks."""
    return [
        {
            "question": "Which page is currently open?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "What was the last successful action?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "Which selector failed?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "What is the current user goal?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "Which element should we NOT retry?",
            "type": "reasoning",
            "importance": "high"
        },
    ]


def research_probes(task: dict[str, Any], context: list[dict]) -> list[dict]:
    """Generate probe questions for research tasks."""
    return [
        {
            "question": "Which source was most relevant so far?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "What question remains unanswered?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "Which constraint must the final answer follow?",
            "type": "recall",
            "importance": "critical"
        },
        {
            "question": "What claim has already been verified?",
            "type": "recall",
            "importance": "high"
        },
        {
            "question": "Which sources should we avoid re-checking?",
            "type": "reasoning",
            "importance": "medium"
        },
    ]


def get_probes(task_type: str, task: dict[str, Any], context: list[dict]) -> list[dict]:
    """Get probes for a task based on its category."""
    if "coding" in task_type.lower():
        return coding_probes(task, context)
    elif "browser" in task_type.lower():
        return browser_probes(task, context)
    elif "research" in task_type.lower():
        return research_probes(task, context)
    else:
        return []
