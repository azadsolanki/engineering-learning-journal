# Kedro Feature Engineering Pipeline — POC

Same pipeline as the other POCs — built with Kedro, the ML pipeline framework by QuantumBlack (McKinsey).

## What this POC covers

| Concept | Where |
|---|---|
| Plain-function nodes (no decorators) | `src/nodes/features.py` |
| `Pipeline` + `node()` wiring by dataset name | `src/pipeline.py` |
| DataCatalog — decouples nodes from file paths | `conf/base/catalog.yml` |
| `SequentialRunner` for local execution | `src/run.py` |
| File-based caching via catalog datasets | Run twice to observe |

## Pipeline node graph

```
orders_csv (CSVDataset)
        │
   ingest_raw_data
        │
   raw_orders (ParquetDataset)
        │
        ├──► compute_aggregation_features → agg_features
        ├──► compute_temporal_features   → temporal_features
        └──► compute_category_features   → category_features
                        │
                  merge_features
                        │
              customer_feature_store (ParquetDataset)
```

Dataset names (e.g. `raw_orders`) are the contract between nodes — not function calls, not imports.

## Kedro's key abstraction: the DataCatalog

Kedro's most distinctive feature is that **nodes never reference file paths**. Instead they declare inputs/outputs by name, and the DataCatalog resolves them:

```yaml
# conf/base/catalog.yml
raw_orders:
  type: pandas.ParquetDataset
  filepath: data/02_intermediate/raw_orders.parquet
```

```python
# src/pipeline.py — node just names its datasets
node(func=ingest_raw_data, inputs="orders_csv", outputs="raw_orders")
```

Swap `ParquetDataset` for `SQLTableDataset` or `SparkDataset` — the node code changes nothing.

## Caching model

Kedro's caching is identical to Luigi: **output file existence**.

- Each dataset in `catalog.yml` has a `filepath`
- If that file exists, the `SequentialRunner` loads it instead of re-running the node
- Delete the file to force recomputation of that node and its dependents

```bash
# Run once — all nodes execute
PYTHONPATH=. python src/run.py

# Run again — catalog files exist, so nodes are skipped
PYTHONPATH=. python src/run.py

# Bust cache for one node
rm data/02_intermediate/agg_features.parquet
PYTHONPATH=. python src/run.py  # only agg + merge re-run
```

## Quickstart

```bash
cd projects/09-miscellaneous/kedro-feature-pipeline

# 1. Install deps
uv pip install -r requirements.txt

# 2. Run the pipeline
PYTHONPATH=. python src/run.py

# 3. Run a single node
PYTHONPATH=. python src/run.py --only merge_features

# 4. (Optional) Use the full Kedro CLI (requires kedro project scaffold)
kedro run
kedro run --node compute_aggregation_features
kedro viz   # interactive pipeline graph in browser
```

## Project structure

```
kedro-feature-pipeline/
├── conf/
│   └── base/
│       └── catalog.yml         ← DataCatalog: dataset names → storage
├── data/
│   ├── 01_raw/
│   │   └── orders.csv          ← input
│   ├── 02_intermediate/        ← intermediate datasets (cached)
│   └── 03_output/
│       └── customer_feature_store.parquet  ← final output
├── src/
│   ├── nodes/
│   │   └── features.py         ← pure Python functions (no framework imports)
│   ├── pipeline.py             ← node wiring
│   └── run.py                  ← local runner entrypoint
└── requirements.txt
```

## Kedro vs Airflow

| | Kedro | Airflow |
|---|---|---|
| **Unit of work** | Pure Python function (no base class) | `Operator` class |
| **Data passing** | DataCatalog (named datasets, file/DB-backed) | XComs (size-limited) |
| **Caching** | Output file existence (via catalog) | Not built-in |
| **Configuration** | `catalog.yml`, `parameters.yml` — YAML-first | Python DAG file |
| **Local dev** | `kedro run` — no scheduler needed | Full Airflow stack |
| **UI** | `kedro viz` — interactive pipeline graph | Full Airflow UI |
| **Ecosystem** | ML-focused plugins (MLflow, Great Expectations) | Huge operator library |

## Kedro vs the other POC tools

| | Kedro | Luigi | Prefect | Flyte | Dagster | Metaflow |
|---|---|---|---|---|---|---|
| **Node definition** | Pure function | Task class | `@task` | `@task` | `@asset` | `@step` |
| **Data wiring** | DataCatalog (YAML) | `LocalTarget` | Return values | Return values | IO manager | `self.*` |
| **Caching** | File existence | File existence | Input hash + TTL | Input hash | Lineage | Step checkpoint |
| **Config** | YAML-driven | Code-driven | Code-driven | Code-driven | Code-driven | Code-driven |
| **Best for** | ML projects, reusable data pipelines, team standardisation | Simple batch ETL | General Python flows | Typed ML pipelines | Data observability | Experiment tracking |
