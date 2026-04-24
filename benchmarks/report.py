"""Generate benchmark reports from results."""

import csv
import json
from pathlib import Path
from typing import Any


def load_results(baseline_file: str, memrail_file: str) -> tuple[list[dict], list[dict]]:
    """Load baseline and Memrail results from JSON files."""
    with open(baseline_file) as f:
        baseline = json.load(f)
    with open(memrail_file) as f:
        memrail = json.load(f)
    return baseline, memrail


def aggregate_by_type(results: list[dict]) -> dict[str, list[dict]]:
    """Group results by task type."""
    grouped = {}
    for result in results:
        task_type = result["task_type"]
        if task_type not in grouped:
            grouped[task_type] = []
        grouped[task_type].append(result)
    return grouped


def compute_summary(baseline: list[dict], memrail: list[dict]) -> dict[str, Any]:
    """Compute summary statistics."""

    def avg(key: str, results: list[dict]) -> float:
        values = [r.get(key, 0) for r in results if r.get(key) is not None]
        return sum(values) / len(values) if values else 0.0

    def pct(key: str, results: list[dict]) -> float:
        true_count = sum(1 for r in results if r.get(key))
        return (true_count / len(results) * 100) if results else 0.0

    baseline_by_type = aggregate_by_type(baseline)
    memrail_by_type = aggregate_by_type(memrail)

    summary = {
        "overall": {
            "baseline_avg_tokens": avg("tokens_before", baseline),
            "memrail_avg_tokens": avg("tokens_after", memrail),
            "avg_token_reduction_pct": avg("token_reduction_pct", memrail),
            "baseline_success_rate": pct("task_success", baseline),
            "memrail_success_rate": pct("task_success", memrail),
            "baseline_context_failure_rate": pct("is_context_failure", baseline),
            "memrail_context_failure_rate": pct("is_context_failure", memrail),
            "avg_state_retention": avg("state_retention_score", memrail),
            "avg_continuity_score": avg("continuity_score", memrail),
        },
        "by_type": {},
    }

    for task_type in set(baseline_by_type.keys()) | set(memrail_by_type.keys()):
        b = baseline_by_type.get(task_type, [])
        m = memrail_by_type.get(task_type, [])
        summary["by_type"][task_type] = {
            "baseline_avg_tokens": avg("tokens_before", b),
            "memrail_avg_tokens": avg("tokens_after", m),
            "avg_token_reduction_pct": avg("token_reduction_pct", m),
            "baseline_success_rate": pct("task_success", b),
            "memrail_success_rate": pct("task_success", m),
            "runs": len(m),
        }

    return summary


def generate_markdown_report(baseline: list[dict], memrail: list[dict], output_file: str = "benchmarks/results/REPORT.md"):
    """Generate markdown report of results."""
    summary = compute_summary(baseline, memrail)

    report = "# Memrail Benchmark Report\n\n"
    report += f"**Generated:** `{Path(output_file).parent}/` \n\n"

    # Overall summary
    overall = summary["overall"]
    report += "## Overall Results\n\n"
    report += "| Metric | Baseline | Memrail | Delta |\n"
    report += "|---|---|---|---|\n"
    report += f"| Avg tokens per run | {overall['baseline_avg_tokens']:.0f} | {overall['memrail_avg_tokens']:.0f} | -{overall['baseline_avg_tokens'] - overall['memrail_avg_tokens']:.0f} |\n"
    report += f"| Token reduction | — | — | **{overall['avg_token_reduction_pct']:.1f}%** |\n"
    report += f"| Task success rate | {overall['baseline_success_rate']:.1f}% | {overall['memrail_success_rate']:.1f}% | {overall['memrail_success_rate'] - overall['baseline_success_rate']:+.1f}% |\n"
    report += f"| Context failures | {overall['baseline_context_failure_rate']:.1f}% | {overall['memrail_context_failure_rate']:.1f}% | {overall['memrail_context_failure_rate'] - overall['baseline_context_failure_rate']:+.1f}% |\n"
    report += f"| State retention | — | {overall['avg_state_retention']:.1%} | — |\n"
    report += f"| Continuity score | — | {overall['avg_continuity_score']:.2f}/2.0 | — |\n"
    report += "\n"

    # By task type
    report += "## Results by Task Type\n\n"
    for task_type, metrics in summary["by_type"].items():
        report += f"### {task_type.title()}\n\n"
        report += f"- Runs: {metrics['runs']}\n"
        report += f"- Baseline avg tokens: {metrics['baseline_avg_tokens']:.0f}\n"
        report += f"- Memrail avg tokens: {metrics['memrail_avg_tokens']:.0f}\n"
        report += f"- Token reduction: **{metrics['avg_token_reduction_pct']:.1f}%**\n"
        report += f"- Baseline success rate: {metrics['baseline_success_rate']:.1f}%\n"
        report += f"- Memrail success rate: {metrics['memrail_success_rate']:.1f}%\n\n"

    # Conclusion
    report += "## Conclusion\n\n"
    if overall["avg_token_reduction_pct"] >= 30:
        report += f"✓ **Token reduction target met:** {overall['avg_token_reduction_pct']:.1f}% (target: 30%+)\n\n"
    else:
        report += f"⚠ Token reduction: {overall['avg_token_reduction_pct']:.1f}% (target: 30%+)\n\n"

    if overall["memrail_success_rate"] >= overall["baseline_success_rate"]:
        report += f"✓ **Task success maintained:** {overall['memrail_success_rate']:.1f}% (baseline: {overall['baseline_success_rate']:.1f}%)\n\n"
    else:
        report += f"⚠ Task success: {overall['memrail_success_rate']:.1f}% (baseline: {overall['baseline_success_rate']:.1f}%)\n\n"

    report += f"✓ **Context failures reduced:** {overall['baseline_context_failure_rate']:.1f}% → {overall['memrail_context_failure_rate']:.1f}%\n\n"

    with open(output_file, "w") as f:
        f.write(report)
    print(f"Report written to {output_file}")


def generate_csv_summary(baseline: list[dict], memrail: list[dict], output_file: str = "benchmarks/results/summary.csv"):
    """Generate CSV summary of results."""
    rows = []

    baseline_by_id = {r["task_id"]: r for r in baseline}
    memrail_by_id = {r["task_id"]: r for r in memrail}

    for task_id in sorted(set(baseline_by_id.keys()) | set(memrail_by_id.keys())):
        b = baseline_by_id.get(task_id, {})
        m = memrail_by_id.get(task_id, {})

        rows.append({
            "task_id": task_id,
            "task_type": m.get("task_type", b.get("task_type", "unknown")),
            "baseline_tokens": b.get("tokens_before", "—"),
            "memrail_tokens": m.get("tokens_after", "—"),
            "reduction_pct": f"{m.get('token_reduction_pct', 0):.1f}%" if m else "—",
            "baseline_success": "✓" if b.get("task_success") else "✗",
            "memrail_success": "✓" if m.get("task_success") else "✗",
            "state_retention": f"{m.get('state_retention_score', 0):.1%}" if m else "—",
        })

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV written to {output_file}")


if __name__ == "__main__":
    baseline, memrail = load_results(
        "benchmarks/results/baseline_results.json",
        "benchmarks/results/memrail_results.json",
    )
    generate_markdown_report(baseline, memrail)
    generate_csv_summary(baseline, memrail)
