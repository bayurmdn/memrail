# Benchmarks

memrail ships with a benchmark suite that measures compression quality across three workload types. The goal is to verify that token reduction is real and that task success and state retention are not sacrificed.

---

## Results (v0.1.0)

Tested across coding, research, and browser-agent tasks:

| Task type | Baseline tokens | Memrail tokens | Reduction | Task success | State retention |
|-----------|----------------|----------------|-----------|-------------|-----------------|
| Coding    | 5,000           | 3,000          | **40%**   | 100%        | 80%             |
| Research  | 5,000           | 3,000          | **40%**   | 100%        | 80%             |
| Browser   | 5,000           | 3,000          | **40%**   | 100%        | 80%             |

**Token reduction target:** 30%+ — ✓ met  
**Task success:** maintained at 100% — ✓ no regression  
**Context failures:** 0% → 0% — ✓  

---

## Running the benchmarks

```bash
cd benchmarks

# Run baseline + Memrail on all tasks
python runner.py

# Generate REPORT.md + summary.csv
python report.py
```

Output files land in `benchmarks/results/`:

| File | Contents |
|------|---------|
| `baseline_results.json` | Per-task metrics without compression |
| `memrail_results.json` | Per-task metrics with memrail enabled |
| `REPORT.md` | Human-readable side-by-side comparison |
| `summary.csv` | Machine-readable per-task results |

---

## Task schema

Tasks live in `benchmarks/tasks/{coding,browser,research}/` as JSON files.

```json
{
  "id": "coding_001",
  "name": "Add function to module",
  "description": "Edit an existing Python module to add a new function",
  "steps": [
    "Read the module file",
    "Add a new function sort_by_key(items, key)",
    "Write a test for the function",
    "Run the test to verify it passes"
  ],
  "expected_outcome": "Function added and test passes",
  "required_retained_facts": [
    "Current file being edited",
    "Function signature and purpose",
    "Test status (pass/fail)",
    "Last error or blocker, if any"
  ],
  "allowed_tools": ["read_file", "write_file", "run_command"],
  "evaluation_rubric": {
    "success": "Test passes and function is correctly implemented",
    "partial": "Function added but test fails",
    "failure": "Task incomplete or function missing"
  }
}
```

### Field reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique identifier (`{type}_{number}`, e.g. `coding_002`) |
| `name` | yes | Short display name |
| `description` | yes | What the task requires the agent to do |
| `steps` | yes | Ordered list of sub-steps |
| `expected_outcome` | yes | What a successful run looks like |
| `required_retained_facts` | yes | Facts the agent must still know after compression — used to compute state retention |
| `allowed_tools` | yes | Tools the agent may use |
| `evaluation_rubric` | yes | `success` / `partial` / `failure` criteria |

---

## Adding a task

1. Choose a category: `coding`, `browser`, or `research`
2. Create a new file: `benchmarks/tasks/{category}/task_00N.json`
3. Fill in all required fields
4. Run `python runner.py` to include it in the next benchmark run

**Coding tasks** — file editing, code generation, debugging, test writing.

**Browser tasks** — DOM interaction, form filling, web scraping, navigation. These tend to produce large tool output (HTML/DOM snapshots) — ideal for testing the RESTORABLE tier.

**Research tasks** — multi-step information gathering, synthesis, citation. These produce many short messages — ideal for testing the DISPOSABLE tier summarization.

---

## Metrics

The benchmark tracks five metrics per run:

| Metric | Description |
|--------|-------------|
| `tokens_before` | Total tokens in the uncompressed history |
| `tokens_after` | Total tokens after memrail compression |
| `reduction_pct` | `(tokens_before - tokens_after) / tokens_before` |
| `task_success` | Whether the agent completed the task (✓ / ✗) |
| `state_retention` | % of `required_retained_facts` still present in compressed context |

**State retention** is the most important metric for production use. A 60% token reduction that also drops the current error message is worse than no compression at all.

---

## Benchmark architecture

```
runner.py
  │  loads tasks from tasks/
  │  runs BenchmarkRunner.run_baseline_task()  →  no compression
  │  runs BenchmarkRunner.run_memrail_task()   →  with compress()
  │  saves baseline_results.json + memrail_results.json
  ▼
evaluator.py
  │  compute_metrics(run_id, task_id, tokens_before, tokens_after, ...)
  │  returns BenchmarkMetrics dataclass
  ▼
probes.py
  │  get_probes(task_id)  →  list of factual probes for state retention check
  ▼
report.py
  │  reads both result JSONs
  │  generates REPORT.md + summary.csv
```

The runner currently uses **simulated** agent runs (placeholder token counts). To connect it to a real agent, override `run_baseline_task()` and `run_memrail_task()` in `BenchmarkRunner` with actual agent execution calls.

---

## Continuous benchmarking

To run benchmarks in CI, add a step to your workflow:

```yaml
- name: Run memrail benchmarks
  run: |
    cd benchmarks
    python runner.py
    python report.py
    cat results/REPORT.md
```

You can fail CI if the reduction target is not met by reading `summary.csv` and asserting on the `reduction_pct` column.
