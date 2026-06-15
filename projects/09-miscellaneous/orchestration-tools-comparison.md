# Python Orchestration Tools — Comparison

Covers **Flyte**, **Prefect**, **Dagster**, **Luigi**, **Metaflow**, **Kedro**, **Airflow**, **Hamilton**, and **ZenML** using the same feature engineering pipeline across all nine.  
Each tool ingests the same e-commerce dataset and produces the same 21-feature Parquet artifact.

POCs:
- [flyte-feature-pipeline](./flyte-feature-pipeline/)
- [prefect-feature-pipeline](./prefect-feature-pipeline/)
- [dagster-feature-pipeline](./dagster-feature-pipeline/)
- [luigi-feature-pipeline](./luigi-feature-pipeline/)
- [metaflow-feature-pipeline](./metaflow-feature-pipeline/)
- [kedro-feature-pipeline](./kedro-feature-pipeline/)
- [airflow-feature-pipeline](./airflow-feature-pipeline/)
- [hamilton-feature-pipeline](./hamilton-feature-pipeline/)
- [zenml-feature-pipeline](./zenml-feature-pipeline/)

---

## Quick-pick guide

| If you need… | Use |
|---|---|
| Zero infra, file-based checkpointing, dead simple | **Luigi** |
| Python-native flows, local caching out of the box, lightweight server | **Prefect** |
| ML pipelines, strong typing, cross-cluster artifact sharing | **Flyte** |
| Data asset lineage, observability, freshness-based scheduling | **Dagster** |
| ML experiments, failure-tolerant pipelines, fan-out parallelism | **Metaflow** |
| Reusable nodes, YAML-driven data catalog, team ML standardisation | **Kedro** |
| Industry-standard scheduling, massive operator ecosystem | **Airflow** |
| DAG inferred from function signatures, zero framework coupling | **Hamilton** |
| Flyte-style caching locally, pluggable infra stack | **ZenML** |

---

## Full comparison

| Dimension | Luigi | Prefect | Flyte | Dagster | Metaflow | Kedro | Airflow | Hamilton | ZenML |
|---|---|---|---|---|---|---|---|---|---|
| **Core abstraction** | `Task` class | `@task` function | `@task` function | `@asset` | `@step` method | Pure function + DataCatalog | `@task` (TaskFlow) | Function name = output | `@step` function |
| **Pipeline definition** | `requires()` + `output()` + `run()` | `@flow` + `.submit()` | `@workflow` DAG | Asset graph | `FlowSpec` class | `pipeline([node(...)])` | `@dag` | `Driver.execute()` | `@pipeline` |
| **Mental model** | Steps produce files | Functions in a flow | Typed computational graph | Assets that materialise | Steps on a class | Nodes wired by name | Scheduled task graph | Functions are a DAG | Steps on a stack |
| **Caching mechanism** | File exists → skip | Input hash + TTL | Input hash + `cache_version` | Lineage + freshness | Step checkpoint (failure resume) | File exists → skip | None built-in | Result store (opt-in) | Input hash (local) |
| **Caching works locally?** | Yes — filesystem | Yes — `~/.prefect/storage/` | No — needs cluster | Ephemeral | Yes — `.metaflow/` | Yes — catalog files | No | Yes — cache dir | Yes — `~/.zenml/` |
| **Cache invalidation** | Delete output file | TTL expires or inputs change | Bump `cache_version` | Upstream rematerialised | Start a new run | Delete output file | Manual skip logic | Delete cache dir | Inputs change |
| **Parallelism** | `--workers N` flag | `.submit()` + task runner | Implicit — auto-parallel | Implicit — asset graph | `self.next(a, b, c)` fan-out | `ParallelRunner` | Implicit from wiring | Implicit from graph | Sequential (local) |
| **Data passing** | Files via `LocalTarget` | Return values | Typed return values | Return values + IO managers | `self.*` (auto-serialised) | Named datasets (catalog) | XCom (DB, size-limited) | Return values | Return values |
| **Typed I/O** | No — files only | Python types (unenforced) | Strong — `FlyteFile` etc. | Python types + IO managers | Python types (unenforced) | Python types (unenforced) | No — XCom is untyped | Python types (unenforced) | Python types (unenforced) |
| **Local dev** | `local_scheduler=True` | `python flow.py` | `pyflyte run` | `materialize()` | `python flow.py run` | `kedro run` | Full stack required | `python run.py` | `python pipeline.py` |
| **Server needed locally?** | No | No | No (caching needs cluster) | No | No | No | Yes | No | No |
| **UI** | Minimal (luigid) | Prefect UI (lightweight) | Flyte UI (full) | Dagster UI (rich) | None built-in | `kedro viz` | Full Airflow UI | None built-in | ZenML Dashboard |
| **Observability** | Task status only | Flow + task run history | Task runs, artifacts | Asset lineage, metadata, versions | Run history + artifact access | Node run history | Task run history | DAG visualisation | Step runs, artifact store |
| **Config approach** | Code-driven | Code-driven | Code-driven | Code-driven | `Parameter` CLI args | YAML (`catalog.yml`) | Code-driven | `inputs={}` dict | Code-driven |
| **Ecosystem** | Small, stable | Growing | ML-focused | Data-focused | Netflix ML | ML + data plugins | Massive operator library | Micro-framework | ML stack integrations |
| **Learning curve** | Very low | Low | Steeper | Medium | Low-medium | Medium | Medium | Low | Low-medium |
| **Age / maturity** | 2012 — very mature | 2018 | 2019 | 2019 | 2018 | 2019 | 2015 — most mature | 2022 | 2021 |
| **Origin** | Spotify | Community | Lyft / Union.ai | Elementl | Netflix | QuantumBlack | Airbnb | DAGWorks | Community |

---

## Caching: how each tool decides to skip a task

The most important conceptual difference across all nine tools.

### Luigi & Kedro — file existence
```python
# Luigi
class AggregationFeatures(luigi.Task):
    def output(self):
        return luigi.LocalTarget("output/agg_features.parquet")
    # run() only called if file does NOT exist

# Kedro (catalog.yml)
# agg_features:
#   type: pandas.ParquetDataset
#   filepath: data/02_intermediate/agg_features.parquet
# → node skipped if filepath already exists
```
**Rule:** output file present → done.  
**Limitation:** no awareness of whether upstream data changed.

---

### Prefect — input hash + TTL
```python
@task(cache_policy=INPUTS, cache_expiration=timedelta(hours=24))
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame: ...
```
**Rule:** hash all inputs → if match and within TTL → return cached result. Works locally, persists across runs.

---

### Flyte — input hash + cache version
```python
@task(cache=True, cache_version="1.0")
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame: ...
```
**Rule:** same as Prefect + explicit version string. Bump `"1.0"` → `"1.1"` to force recompute.  
**Requires Flyte cluster** for real caching — local runs always execute.

---

### Dagster — asset freshness / lineage
```python
@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=60))
def aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame: ...
```
**Rule:** skip if asset is "fresh" relative to upstream materialisation timestamps — not input content.  
**Philosophy:** "Is this asset stale?" not "Did the data change?"

---

### Metaflow — step-level checkpoint (failure resume)
```python
@step
def agg_features(self):
    self.result = compute(self.raw)
    self.next(self.join_features)
# Artifacts stored in .metaflow/<run-id>/
```
**Rule:** not skip-on-same-inputs — step artifacts are checkpointed per run. `resume` re-runs from a failed step.  
**Philosophy:** failure recovery, not idempotency.

---

### Airflow — no built-in caching
```python
@task()
def compute_agg_features(raw_path: str) -> str:
    # Must implement manually — check if output exists, skip if so
    if Path("output/agg.parquet").exists():
        return "output/agg.parquet"
    # ... compute ...
```
**Rule:** none. Airflow has no native task caching — every run re-executes every task.  
**Workarounds:** `ShortCircuitOperator`, skip logic inside the task, or external state checks.

---

### Hamilton — result store (opt-in)
```python
from hamilton.plugins import h_cache

dr = driver.Builder().with_modules(features).with_cache(h_cache.SmartCacheAdapter("cache/")).build()
# Second execute() with same inputs → loads from cache/
```
**Rule:** configurable — off by default. Add `with_cache()` to the Driver builder to enable.  
**Note:** without a cache adapter the graph always recomputes.

---

### ZenML — input hash (local, like Prefect)
```python
@step(enable_cache=True)
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame: ...
```
**Rule:** same as Prefect — hash inputs, return cached artifact if match. Works locally out of the box via `~/.zenml/`.  
**Advantage over Flyte:** no cluster needed for local caching.

---

## Code style: same computation in all nine tools

Per-customer aggregation feature — the pattern each tool uses:

**Luigi**
```python
class AggregationFeatures(luigi.Task):
    def requires(self): return IngestData()
    def output(self):   return luigi.LocalTarget("output/agg.parquet")
    def run(self):
        df = pd.read_parquet(self.input().path)
        df.groupby("customer_id").agg(...).to_parquet(self.output().path)
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

**Metaflow**
```python
@step
def agg_features(self):
    self.result = self.raw.groupby("customer_id").agg(...).reset_index()
    self.next(self.join_features)
```

**Kedro**
```python
# Pure function — no framework imports at all
def compute_aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    return raw_orders.groupby("customer_id").agg(...).reset_index()
```

Kedro and Hamilton nodes are the most portable — zero framework imports.  
Metaflow is unique in being class-method based with `self` for state.  
Prefect, Flyte, and ZenML look nearly identical — the difference is the runtime and caching backend.  
Dagster adds observability metadata as a first-class concern.  
Airflow requires passing file paths via XCom rather than DataFrames.

**Airflow**
```python
@task()
def compute_agg_features(raw_path: str) -> str:   # path via XCom, not DataFrame
    df = pd.read_parquet(raw_path)
    result = df.groupby("customer_id").agg(...).reset_index()
    path = "/tmp/agg.parquet"
    result.to_parquet(path)
    return path
```

**Hamilton**
```python
# Pure function — zero framework imports, same as Kedro
def aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    return raw_orders.groupby("customer_id").agg(...).reset_index()
```

**ZenML**
```python
@step(enable_cache=True)
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("customer_id").agg(...).reset_index()
```

---

## When NOT to use each tool

| Tool | Avoid when… |
|---|---|
| **Luigi** | You need content-aware caching, dynamic DAGs, or a rich UI |
| **Prefect** | You need strong typing across tasks or ML artifact management |
| **Flyte** | You can't run Kubernetes, or your team prefers minimal infra |
| **Dagster** | Your pipelines are compute-jobs (not asset-producing), or you want simplicity |
| **Metaflow** | You need cross-run idempotency (not just failure resume), or a UI |
| **Kedro** | You want minimal config files, or your pipeline is a one-off script |
| **Airflow** | You want simple local dev, built-in caching, or small team with no ops budget |
| **Hamilton** | You need scheduling, a UI, or distributed execution out of the box |
| **ZenML** | You need a large operator ecosystem or your team is already on Airflow/Prefect |

---

## Airflow vs the other eight

| | Airflow | The other eight tools |
|---|---|---|
| **Caching** | None built-in | Built-in — each model differs (see above) |
| **Data passing** | XComs (DB, size-limited, untyped) | Native — in-memory or typed artifacts |
| **Local dev** | Full stack (scheduler + webserver + DB) | `python script.py` or lightweight runner |
| **Paradigm** | Task-centric, DAG-as-code | Varies — function, asset, step, node |
| **Operator ecosystem** | Massive (S3, GCS, Snowflake, dbt, …) | Smaller — more DIY |

Airflow dominates on ecosystem breadth and team familiarity.  
Every other tool in this series beats it on local dev experience and built-in caching.
