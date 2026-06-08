# Luigi Feature Engineering Pipeline — POC

Same pipeline as the [Flyte](../flyte-feature-pipeline/), [Prefect](../prefect-feature-pipeline/), and [Dagster](../dagster-feature-pipeline/) POCs — built with Luigi, the OG Python pipeline library by Spotify.

## What this POC covers

| Concept | Where |
|---|---|
| `luigi.Task` class-based pipeline definition | `src/tasks/pipeline.py` |
| `output()` → `LocalTarget` — filesystem-based caching | Every task |
| `requires()` for dependency wiring | Every task |
| `luigi.build()` local execution | `src/pipeline.py` |
| Built-in idempotency via output file existence check | Run twice to observe |

## Pipeline dependency graph

```
IngestData
        │
        ├──► AggregationFeatures
        ├──► TemporalFeatures
        └──► CategoryFeatures
                    │
              MergeFeatures
                    │
             FeatureStore  →  output/04_feature_store.parquet
```

Each arrow is a `requires()` dependency. Luigi resolves the graph and runs tasks in topological order.

## Caching in Luigi

Luigi's caching is the **simplest** of all tools — and the most transparent:

```python
class AggregationFeatures(luigi.Task):
    def output(self):
        return luigi.LocalTarget("output/02_agg_features.parquet")

    def run(self):
        ...  # only called if output() file does NOT exist
```

**Rule:** If `output().path` exists on disk → task is `DONE`, skip `run()`. No hash, no TTL, no server.

```
Run 1:  Scheduled 6 tasks → 6 ran successfully
Run 2:  Scheduled 1 tasks → 0 ran  (all outputs exist)
```

To force a task to rerun — just delete its output file:

```bash
rm output/02_agg_features.parquet
python src/pipeline.py   # only AggregationFeatures + downstream rerun
```

This simplicity is both Luigi's strength and limitation. It works perfectly for batch ETL, but gives you no insight into *why* a file was produced or *when* inputs changed.

## Quickstart

```bash
cd projects/09-miscellaneous/luigi-feature-pipeline

# 1. Install deps
uv pip install -r requirements.txt

# 2. Run the pipeline (data/orders.csv already included)
PYTHONPATH=. python src/pipeline.py

# 3. Run again — watch all tasks report DONE immediately (cached)
PYTHONPATH=. python src/pipeline.py

# 4. Bust cache for one step and rerun only that branch
rm output/02_agg_features.parquet
PYTHONPATH=. python src/pipeline.py
```

## Project structure

```
luigi-feature-pipeline/
├── data/
│   └── orders.csv              ← same synthetic dataset as other POCs
├── output/                     ← task outputs land here (gitignored)
│   ├── 01_raw.parquet
│   ├── 02_agg_features.parquet
│   ├── 02_temporal_features.parquet
│   ├── 02_category_features.parquet
│   ├── 03_merged_features.parquet
│   └── 04_feature_store.parquet
├── src/
│   ├── tasks/
│   │   └── pipeline.py         ← all Task class definitions
│   └── pipeline.py             ← luigi.build() entrypoint
└── requirements.txt
```

## Luigi vs Airflow

| | Luigi | Airflow |
|---|---|---|
| **Unit of work** | `Task` class with `requires` / `output` / `run` | `Operator` class with `execute()` |
| **Caching** | Built-in — output file existence | Not built-in |
| **Scheduler** | Optional central scheduler; `local_scheduler=True` for local | Required — Airflow scheduler always needed |
| **UI** | Minimal (luigid web UI) | Full-featured |
| **Parallelism** | Via `--workers N` flag | Via executor config |
| **Ecosystem** | Small, stable | Huge, active |
| **Maturity** | Very mature, stable API, low activity | Battle-tested, actively developed |

## Luigi vs Flyte / Prefect / Dagster (same pipeline)

| | Luigi | Flyte | Prefect | Dagster |
|---|---|---|---|---|
| **Abstraction** | `Task` class | `@task` function | `@task` function | `@asset` |
| **Caching key** | Output file existence | Input hash | Input hash + TTL | Lineage + freshness |
| **Setup** | Zero — pure Python | Cluster for real caching | `~/.prefect/` storage | Asset catalog |
| **Observability** | Minimal | Flyte UI + metadata | Prefect UI | Rich asset catalog |
| **Best for** | Simple batch ETL, minimal ops | ML pipelines | General Python flows | Data-asset workflows |
| **Learning curve** | Very low | Steeper | Low | Medium |

**Bottom line:** Luigi is the right tool when you want zero infrastructure, clear file-based checkpointing, and a pipeline that a new engineer can understand in 5 minutes.
