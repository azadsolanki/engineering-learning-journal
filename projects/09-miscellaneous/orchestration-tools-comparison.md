# Python Orchestration Tools — Comparison

Covers **Flyte**, **Prefect**, **Dagster**, and **Luigi** using the same feature engineering pipeline across all four.  
Each tool ingests the same e-commerce dataset and produces the same 21-feature Parquet artifact.

POCs:
- [flyte-feature-pipeline](./flyte-feature-pipeline/)
- [prefect-feature-pipeline](./prefect-feature-pipeline/)
- [dagster-feature-pipeline](./dagster-feature-pipeline/)
- [luigi-feature-pipeline](./luigi-feature-pipeline/)

---

## Quick-pick guide

| If you need… | Use |
|---|---|
| Zero infra, file-based checkpointing, dead simple | **Luigi** |
| Python-native flows, local caching out of the box, lightweight server | **Prefect** |
| ML pipelines, strong typing, cross-cluster artifact sharing | **Flyte** |
| Data asset lineage, observability, freshness-based scheduling | **Dagster** |

---

## Full comparison

| Dimension | Luigi | Prefect | Flyte | Dagster |
|---|---|---|---|---|
| **Core abstraction** | `Task` class | `@task` function | `@task` function | `@asset` (data artifact) |
| **Pipeline definition** | `requires()` + `output()` + `run()` | `@flow` with `.submit()` | `@workflow` DAG | Asset graph + `Definitions` |
| **Mental model** | Steps that produce files | Functions in a flow | Typed computational graph | Assets that get materialised |
| **Caching mechanism** | Output file exists → skip | Input hash + TTL | Input hash + `cache_version` | Lineage + freshness policy |
| **Caching works locally?** | Yes — filesystem | Yes — `~/.prefect/storage/` | No — needs datacatalog | Ephemeral in `materialize()` |
| **Cache invalidation** | Delete the output file | TTL expires or inputs change | Bump `cache_version` | Upstream rematerialised |
| **Parallelism** | `--workers N` CLI flag | `.submit()` + task runner | Implicit — independent tasks auto-parallel | Implicit — asset graph |
| **Typed I/O** | No — files only | Python types (no enforcement) | Strong — `FlyteFile`, `FlyteDirectory` | Python types + IO managers |
| **Local dev** | `local_scheduler=True` | `python flow.py` | `pyflyte run` | `materialize()` |
| **Server needed locally?** | No | No | No (but caching needs cluster) | No |
| **UI** | Minimal (luigid) | Prefect UI (lightweight) | Flyte UI (full) | Dagster UI (rich asset catalog) |
| **Observability** | Task status only | Flow + task run history | Task runs, artifacts | Asset lineage, metadata, versions |
| **Ecosystem** | Small, stable | Growing | ML-focused | Data-engineering focused |
| **Learning curve** | Very low | Low | Steeper | Medium |
| **Age / maturity** | 2012 — very mature | 2018 — modern | 2019 — modern | 2019 — modern |

---

## Caching: how each tool decides to skip a task

This is the most important conceptual difference across the four tools.

### Luigi — file existence
```python
class AggregationFeatures(luigi.Task):
    def output(self):
        return luigi.LocalTarget("output/agg_features.parquet")
    # run() is only called if output().path does NOT exist on disk
```
**Rule:** output file present → done. Bust cache by deleting the file.  
**Limitation:** no awareness of whether inputs changed — only cares that the output file exists.

---

### Prefect — input hash + TTL
```python
from prefect.cache_policies import INPUTS

@task(cache_policy=INPUTS, cache_expiration=timedelta(hours=24))
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    ...
```
**Rule:** hash all inputs → compare to stored hash → if match and within TTL → return cached result.  
**Works locally** — persists to `~/.prefect/storage/` across separate runs.

---

### Flyte — input hash + cache version
```python
@task(cache=True, cache_version="1.0")
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    ...
```
**Rule:** same as Prefect but version-scoped. Bump `cache_version` to force recompute without changing inputs.  
**Requires datacatalog** — local execution runs the task body every time. Full caching needs a Flyte cluster.

---

### Dagster — asset freshness / lineage
```python
@asset(
    auto_materialize_policy=AutoMaterializePolicy.eager(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60),
)
def aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    ...
```
**Rule:** skip if this asset is "fresh" relative to its upstream assets — not based on input content, but on materialisation timestamps.  
**Different philosophy:** Dagster doesn't ask "did the data change?" — it asks "is the asset stale relative to its upstream?"

---

## Code style: same task in all four tools

Computing per-customer aggregations — the pattern each tool uses:

**Luigi**
```python
class AggregationFeatures(luigi.Task):
    csv_path = luigi.Parameter()

    def requires(self): return IngestData(csv_path=self.csv_path)
    def output(self):   return luigi.LocalTarget("output/agg.parquet")
    def run(self):
        df = pd.read_parquet(self.input().path)
        result = df.groupby("customer_id").agg(...).reset_index()
        result.to_parquet(self.output().path, index=False)
```

**Prefect**
```python
@task(cache_policy=INPUTS, cache_expiration=timedelta(hours=24))
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("customer_id").agg(...).reset_index()
```

**Flyte**
```python
@task(cache=True, cache_version="1.0")
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("customer_id").agg(...).reset_index()
```

**Dagster**
```python
@asset(ins={"raw_orders": AssetIn()}, group_name="features")
def aggregation_features(context, raw_orders: pd.DataFrame) -> pd.DataFrame:
    result = raw_orders.groupby("customer_id").agg(...).reset_index()
    context.add_output_metadata({"row_count": MetadataValue.int(len(result))})
    return result
```

Prefect and Flyte look almost identical at the task level — the difference is in the runtime and caching backend.  
Luigi is the most verbose but the most explicit.  
Dagster looks different because assets carry metadata and observability as first-class concerns.

---

## When NOT to use each tool

| Tool | Avoid when… |
|---|---|
| **Luigi** | You need dynamic DAGs, caching based on data content, or a rich UI |
| **Prefect** | You need strong typing across tasks, or ML artifact management |
| **Flyte** | You can't run a Kubernetes cluster, or your team prefers minimal infra |
| **Dagster** | Your pipelines are compute-jobs (not data-asset producing), or you want simplicity |

---

## Airflow vs all four

All four tools in this repo are alternatives to Airflow. The key distinction:

| | Airflow | Luigi / Prefect / Flyte / Dagster |
|---|---|---|
| **Caching** | Not built-in | Built-in (each tool has its own model) |
| **Data passing** | XComs (size-limited, weakly typed) | Native — in-memory or typed artifacts |
| **Local dev** | Requires full Airflow stack | Python script or lightweight runner |
| **Paradigm** | Task-centric, DAG-as-code | Varies — see above |

Airflow remains dominant for breadth of operator integrations and team familiarity. These tools win on developer experience and built-in data awareness.
