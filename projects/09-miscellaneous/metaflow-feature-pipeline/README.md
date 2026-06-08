# Metaflow Feature Engineering Pipeline — POC

Same pipeline as the other POCs — built with Metaflow, Netflix's ML workflow tool.

## What this POC covers

| Concept | Where |
|---|---|
| `FlowSpec` class with `@step` methods | `src/flow.py` |
| `self.next(a, b, c)` fan-out (parallel branches) | `start` step |
| `join` step with `inputs` to merge parallel branches | `join_features` step |
| `self.attribute` for passing data between steps | All steps |
| Step-level checkpointing via `.metaflow/` | `python src/flow.py resume` |
| `Parameter` for CLI arguments | `csv_path` |

## Pipeline step graph

```
start  (ingest)
    │
    ├──► agg_features      (parallel)
    ├──► temporal_features (parallel)
    └──► category_features (parallel)
                │
          join_features  (fan-in, merge)
                │
              end  (save Parquet)
```

Metaflow spawns each parallel branch as a **separate process** — you can see the distinct PIDs in the run log.

## Caching / resume model

Metaflow's approach is **step-level checkpointing**, not input hashing:

- Every step's outputs (`self.*` attributes) are serialised and stored in `.metaflow/<run-id>/`
- If a run fails mid-way, `python src/flow.py resume` re-runs from the failed step, reusing all prior step artifacts
- There is no "skip if inputs unchanged" — resume is failure recovery, not idempotency

```bash
# Run once
python src/flow.py run

# If it fails partway through
python src/flow.py resume   # picks up from the failed step

# Inspect past run artifacts
python src/flow.py show

# Access a specific run's data programmatically
from metaflow import Flow
run = Flow("FeaturePipeline").latest_run
print(run["end"].task.data.output_path)
```

**Key difference from Prefect/Flyte:** Metaflow doesn't skip steps because inputs are the same — it only reuses artifacts from a prior _failed_ run when you explicitly `resume`.

## Quickstart

```bash
cd projects/09-miscellaneous/metaflow-feature-pipeline

# 1. Install deps
uv pip install -r requirements.txt

# 2. Run the pipeline
python src/flow.py run

# 3. Run with a custom CSV
python src/flow.py run --csv_path data/orders.csv

# 4. Inspect past runs
python src/flow.py show

# 5. (Optional) Resume a failed run
python src/flow.py resume
```

## Project structure

```
metaflow-feature-pipeline/
├── data/
│   └── orders.csv          ← same synthetic dataset as other POCs
├── src/
│   └── flow.py             ← FlowSpec with all @step methods
├── .metaflow/              ← created on first run; stores step artifacts
└── requirements.txt
```

## Metaflow vs Airflow

| | Metaflow | Airflow |
|---|---|---|
| **Unit of work** | `@step` method on a `FlowSpec` class | `Operator` class |
| **Parallelism** | `self.next(a, b, c)` native fan-out | Dynamic DAG fan-out |
| **Data passing** | `self.attribute` — automatic serialisation | XComs (size-limited) |
| **Failure recovery** | `resume` command — step-level checkpointing | Task retry with state in DB |
| **Local dev** | `python flow.py run` — zero infra | Full Airflow stack |
| **Cloud scale-out** | Native — `@kubernetes`, `@batch` step decorators | Executor config |
| **ML focus** | Strong — `@conda`, `@resources`, `@card` decorators | General-purpose |

## Metaflow vs the other POC tools

| | Metaflow | Luigi | Prefect | Flyte | Dagster |
|---|---|---|---|---|---|
| **Abstraction** | `@step` on class | `Task` class | `@task` function | `@task` function | `@asset` |
| **Caching** | Step checkpoint (failure resume) | File existence | Input hash + TTL | Input hash + version | Lineage + freshness |
| **Parallelism** | `self.next(a, b, c)` fan-out | `--workers N` | `.submit()` | Implicit | Implicit |
| **Data passing** | `self.*` (auto-serialised) | Files via `LocalTarget` | Return values | Return values | Return values |
| **Best for** | ML experiments, failure-tolerant pipelines | Simple batch ETL | General Python flows | Typed ML pipelines | Data-asset observability |
