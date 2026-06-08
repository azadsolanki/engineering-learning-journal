# Prefect Feature Engineering Pipeline — POC

Same pipeline as the [Flyte POC](../flyte-feature-pipeline/) — built with Prefect to make a direct side-by-side comparison meaningful.

## What this POC covers

| Concept | Where |
|---|---|
| `@task` with `cache_policy=INPUTS` | `src/tasks/features.py` — all three feature tasks |
| `cache_expiration` TTL | Same — set to 24 hours |
| Concurrent task execution via `.submit()` | `src/flow.py` — agg / temporal / category run in parallel |
| `ThreadPoolTaskRunner` | `src/flow.py` — `@flow` decorator |
| `@flow` composition | `src/flow.py` |
| Cache that works locally (no server needed) | `scripts/demo_cache.py` |

## Pipeline DAG

```
ingest_raw_data  (no cache — I/O is fast)
        │
        ├──► compute_aggregation_features  ──┐  ← cached, parallel
        ├──► compute_temporal_features    ──┤  ← cached, parallel
        └──► compute_category_features   ──┘  ← cached, parallel
                        │
                  merge_features  (join + StandardScaler)
                        │
                 save_feature_store  →  Parquet output dir
```

## Caching in depth

Prefect caching is driven by a **cache policy** and a **TTL**.

```python
from prefect.cache_policies import INPUTS

@task(
    cache_policy=INPUTS,           # hash all task inputs to form the cache key
    cache_expiration=timedelta(hours=24),
)
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    ...
```

**Key difference from Flyte:** Prefect's cache works in local execution — no server required. Results are stored in `~/.prefect/storage/` and reused across separate flow runs in the same machine.

| Run | Task status |
|---|---|
| First run (cold) | `Finished in state Completed()` |
| Rerun, same inputs | `Finished in state Cached()` — body skipped |
| After `cache_expiration` | Recomputes and refreshes the cache |

To bust the cache manually:
```bash
rm -rf ~/.prefect/storage/
```

Or change `cache_expiration` to `timedelta(seconds=0)` temporarily.

## Quickstart

```bash
cd projects/09-miscellaneous/prefect-feature-pipeline

# 1. Install deps
pip install -r requirements.txt   # or: uv pip install -r requirements.txt

# 2. Run the pipeline (data/orders.csv already included)
PYTHONPATH=. python src/flow.py

# 3. Run cache demo — two back-to-back runs, second shows Cached() status
PYTHONPATH=. python scripts/demo_cache.py

# 4. (Optional) View run history in the local Prefect UI
prefect server start   # then open http://localhost:4200
PYTHONPATH=. python src/flow.py     # runs appear in the UI
```

## Project structure

```
prefect-feature-pipeline/
├── data/
│   └── orders.csv              ← same synthetic dataset as the Flyte POC
├── scripts/
│   └── demo_cache.py           ← two-run cache demonstration
├── src/
│   ├── tasks/
│   │   ├── ingest.py           ← Task 1: load + validate CSV
│   │   ├── features.py         ← Tasks 2-4: cached feature computation
│   │   └── output.py           ← Tasks 5-6: merge + save Parquet
│   └── flow.py                 ← @flow definition + entrypoint
└── requirements.txt
```

## Prefect vs Airflow

| | Prefect | Airflow |
|---|---|---|
| **Unit of work** | `@task` — plain Python function | `Operator` — class with execute() |
| **DAG definition** | `@flow` — Python control flow, no YAML | Python DAG file with explicit dependencies |
| **Caching** | Built-in — `cache_policy` + TTL, works locally | Not built-in — DIY with sensors/skip logic |
| **Parallelism** | `.submit()` + configurable task runner | Requires explicit fan-out with Dynamic DAGs |
| **Local dev** | `python flow.py` — no scheduler needed | Full Airflow stack (scheduler + webserver) |
| **UI** | `prefect server start` — lightweight | Full Airflow UI — feature-rich but heavy |
| **Dynamic flows** | Native — loops and branches are just Python | Dynamic DAGs possible but verbose |
| **Maturity** | Modern, growing ecosystem | Battle-tested, huge ecosystem |

**When to pick Prefect:** You want Python-native flows, built-in caching, simple local dev, and a lightweight server.

**When to pick Airflow:** Team already uses it, you need its broad operator ecosystem, or you're in a shop standardised on it.

## Prefect vs Flyte (same pipeline)

| | Prefect | Flyte |
|---|---|---|
| **Local caching** | Works — persists to `~/.prefect/storage/` | Metadata only — requires cluster (datacatalog) |
| **Typed I/O** | Standard Python types | Strongly typed — `FlyteFile`, `FlyteDirectory`, etc. |
| **Parallelism** | `.submit()` + task runner | Implicit — independent tasks auto-parallelise |
| **ML/data focus** | General-purpose with ML support | ML-first — native artifact types |
| **Learning curve** | Low — feels like writing Python | Steeper — Flyte concepts (launch plans, versioning) |
