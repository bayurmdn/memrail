"""Compute benchmark metrics from baseline and Memrail runs."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkMetrics:
    """Computed metrics for a single run."""
    run_id: str
    task_id: str
    task_type: str

    # Token metrics
    tokens_before: int
    tokens_after: int
    token_reduction_pct: float

    # Task success
    task_success: bool

    # State retention
    state_retention_score: float
    probes_correct: int
    probes_total: int

    # Continuity
    continuity_score: float  # 0-2

    # Context failures
    context_failures: list[str]
    is_context_failure: bool


def compute_token_reduction(tokens_before: int, tokens_after: int) -> float:
    """Compute token reduction percentage."""
    if tokens_before == 0:
        return 0.0
    return (tokens_before - tokens_after) / tokens_before * 100


def compute_state_retention(probes_correct: int, probes_total: int) -> float:
    """Compute state retention score."""
    if probes_total == 0:
        return 0.0
    return probes_correct / probes_total


def compute_metrics(
    run_id: str,
    task_id: str,
    task_type: str,
    tokens_before: int,
    tokens_after: int,
    task_success: bool,
    probes_correct: int,
    probes_total: int,
    continuity_score: float,
    context_failures: list[str] = None,
) -> BenchmarkMetrics:
    """Compute all metrics for a single run."""
    if context_failures is None:
        context_failures = []

    return BenchmarkMetrics(
        run_id=run_id,
        task_id=task_id,
        task_type=task_type,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        token_reduction_pct=compute_token_reduction(tokens_before, tokens_after),
        task_success=task_success,
        state_retention_score=compute_state_retention(probes_correct, probes_total),
        probes_correct=probes_correct,
        probes_total=probes_total,
        continuity_score=continuity_score,
        context_failures=context_failures,
        is_context_failure=len(context_failures) > 0,
    )


def aggregate_metrics(
    baseline_results: list[BenchmarkMetrics],
    memrail_results: list[BenchmarkMetrics],
) -> dict[str, Any]:
    """Aggregate metrics across all runs."""

    def avg(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def pct(true_count: int, total: int) -> float:
        return (true_count / total * 100) if total > 0 else 0.0

    baseline_success = sum(1 for r in baseline_results if r.task_success)
    memrail_success = sum(1 for r in memrail_results if r.task_success)

    baseline_context_failures = sum(1 for r in baseline_results if r.is_context_failure)
    memrail_context_failures = sum(1 for r in memrail_results if r.is_context_failure)

    return {
        "summary": {
            "total_baseline_runs": len(baseline_results),
            "total_memrail_runs": len(memrail_results),
        },
        "baseline": {
            "avg_tokens": avg([r.tokens_before for r in baseline_results]),
            "task_success_rate": pct(baseline_success, len(baseline_results)),
            "context_failure_rate": pct(baseline_context_failures, len(baseline_results)),
        },
        "memrail": {
            "avg_tokens": avg([r.tokens_after for r in memrail_results]),
            "task_success_rate": pct(memrail_success, len(memrail_results)),
            "context_failure_rate": pct(memrail_context_failures, len(memrail_results)),
            "avg_token_reduction_pct": avg([r.token_reduction_pct for r in memrail_results]),
            "avg_state_retention": avg([r.state_retention_score for r in memrail_results]),
            "avg_continuity_score": avg([r.continuity_score for r in memrail_results]),
        },
        "deltas": {
            "token_reduction_pct": avg([r.token_reduction_pct for r in memrail_results]),
            "task_success_delta_pct": pct(memrail_success, len(memrail_results)) - pct(baseline_success, len(baseline_results)),
            "context_failure_reduction": pct(baseline_context_failures, len(baseline_results)) - pct(memrail_context_failures, len(memrail_results)),
        }
    }
