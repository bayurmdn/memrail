"""Run benchmark tasks with and without Memrail compression."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluator import BenchmarkMetrics, compute_metrics
from probes import get_probes


class BenchmarkRunner:
    """Orchestrate baseline and Memrail benchmark runs."""

    def __init__(self, tasks_dir: str = "benchmarks/tasks", results_dir: str = "benchmarks/results"):
        self.tasks_dir = Path(tasks_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def load_task(self, task_file: str) -> dict[str, Any]:
        """Load a task definition from JSON."""
        with open(self.tasks_dir / task_file) as f:
            return json.load(f)

    def run_baseline_task(self, task: dict[str, Any], task_type: str) -> dict[str, Any]:
        """
        Simulate running a task without Memrail.
        In a real benchmark, this would execute a real agent.
        """
        return {
            "run_id": f"baseline_{task['id']}_{datetime.now().isoformat()}",
            "task_id": task["id"],
            "task_type": task_type,
            "tokens_before": 5000,  # Placeholder
            "tokens_after": 5000,  # No compression
            "task_success": True,
            "probes_correct": 4,
            "probes_total": 5,
            "continuity_score": 2.0,
            "context_failures": [],
        }

    def run_memrail_task(self, task: dict[str, Any], task_type: str) -> dict[str, Any]:
        """
        Simulate running a task with Memrail compression.
        In a real benchmark, this would execute the same agent with compression enabled.
        """
        return {
            "run_id": f"memrail_{task['id']}_{datetime.now().isoformat()}",
            "task_id": task["id"],
            "task_type": task_type,
            "tokens_before": 5000,
            "tokens_after": 3000,  # Compressed by memrail
            "task_success": True,
            "probes_correct": 4,
            "probes_total": 5,
            "continuity_score": 2.0,
            "context_failures": [],
        }

    def run_benchmark(self, task_files: list[str]) -> tuple[list[BenchmarkMetrics], list[BenchmarkMetrics]]:
        """Run all tasks with baseline and Memrail, return results."""
        baseline_results = []
        memrail_results = []

        for task_file in task_files:
            task_type = task_file.split("/")[0]
            task = self.load_task(task_file)

            # Run baseline
            baseline_run = self.run_baseline_task(task, task_type)
            baseline_metrics = compute_metrics(**baseline_run)
            baseline_results.append(baseline_metrics)

            # Run memrail
            memrail_run = self.run_memrail_task(task, task_type)
            memrail_metrics = compute_metrics(**memrail_run)
            memrail_results.append(memrail_metrics)

            print(f"✓ {task['id']}: baseline {baseline_run['tokens_before']} → memrail {memrail_run['tokens_after']}")

        return baseline_results, memrail_results

    def save_results(self, baseline: list[BenchmarkMetrics], memrail: list[BenchmarkMetrics]):
        """Save results to JSON files."""
        baseline_file = self.results_dir / "baseline_results.json"
        memrail_file = self.results_dir / "memrail_results.json"

        with open(baseline_file, "w") as f:
            json.dump([vars(m) for m in baseline], f, indent=2)

        with open(memrail_file, "w") as f:
            json.dump([vars(m) for m in memrail], f, indent=2)

        print(f"Results saved to {baseline_file} and {memrail_file}")


if __name__ == "__main__":
    runner = BenchmarkRunner()

    # Find all task files
    task_files = []
    for cat in ["coding", "browser", "research"]:
        cat_dir = runner.tasks_dir / cat
        if cat_dir.exists():
            for task_file in sorted(cat_dir.glob("*.json")):
                task_files.append(f"{cat}/{task_file.name}")

    if not task_files:
        print("No tasks found. Create task JSONs in benchmarks/tasks/")
        sys.exit(1)

    print(f"Running {len(task_files)} tasks...")
    baseline, memrail = runner.run_benchmark(task_files)
    runner.save_results(baseline, memrail)
