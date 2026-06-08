# Python Orchestration Tools — Comparison

Covers **Flyte**, **Prefect**, **Dagster**, **Luigi**, **Metaflow**, and **Kedro** using the same feature engineering pipeline across all six.  
Each tool ingests the same e-commerce dataset and produces the same 21-feature Parquet artifact.

POCs:
- [flyte-feature-pipeline](./flyte-feature-pipeline/)
- [prefect-feature-pipeline](./prefect-feature-pipeline/)
- [dagster-feature-pipeline](./dagster-feature-pipeline/)
- [luigi-feature-pipeline](./luigi-feature-pipeline/)
- [metaflow-feature-pipeline](./metaflow-feature-pipeline/)
- [kedro-feature-pipeline](./kedro-feature-pipeline/)

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

---

## Full comparison

| Dimension | Luigi | Prefect | Flyte | Dagster | Metaflow | Kedro |
|---|---|---|---|---|---|---|
| **Core abstraction** | `Task` class | `@task` function | `@task` function | `@asset` | `@step` method | Pure function + DataCatalog |
| **Pipeline definition** | `requires()` + `output()` + `run()` | `@flow` + `.submit()` | `@workflow` DAG | Asset graph + `Definitions` | `FlowSpec` class | `pipeline([node(...)])` |
| **Mental model** | Steps that produce files | Functions in a flow | Typed computational graph | Assets that get materialised | Steps on a class | Nodes wired by dataset names |
| **Caching mechanism** | Output file exists → skip | Input hash + TTL | Input hash + `cache_version` | Lineage + freshness policy | Step checkpoint (failure resume) | Output file exists → skip |
| **Caching works locally?** | Yes — filesystem | Yes — `~/.prefect/storage/` | No — needs datacatalog | Ephemeral in `materialize()` | Yes — `.metaflow/` artifacts | Yes — catalog file paths |
| **Cache invalidation** | Delete the output file | TTL expires or inputs change | Bump `cache_version` | Upstream rematerialised | Start a new run | Delete the output file |
| **Parallelism** | `--workers N` flag | `.submit()` + task runner | Implicit — auto-parallel | Implicit — asset graph | `self.next(a, b, c)` fan-out | `ParallelRunner` |
| **Data passing** | Files via `LocalTarget` | Return values | Return values (typed) | Return values + IO managers | `self.*` (auto-serialised) | Named datasets via catalog |
| **Typed I/O** | No — files only | Python types (unenforced) | Strong — `FlyteFile` etc. | Python types + IO managers | Python types (unenforced) | Python types (unenforced) |
| **Local dev** | `local_scheduler=True` | `python flow.py` | `pyflyte run` | `materialize()` | `python flow.py run` | `kedro run` / `python run.py` |
| **Server needed locally?** | No | No | No (caching needs cluster) | No | No | No |
| **UI** | Minimal (luigid) | Prefect UI (lightweight) | Flyte UI (full) | Dagster UI (rich) | None built-in | `kedro viz` (pipeline graph) |
| **Observability** | Task status only | Flow + task run history | Task runs, artifacts | Asset lineage, metadata, versions | Run history + artifact access | Node run history |
| **Config approach** | Code-driven parameters | Code-driven | Code-driven | Code-driven | `Parameter` CLI args | YAML (`catalog.yml`, `params.yml`) |
| **Ecosystem** | Small, stable | Growing | ML-focused | Data-engineering focused | Netflix ML ecosystem | ML + data engineering plugins |
| **Learning curve** | Very low | Low | Steeper | Medium | Low-medium | Medium |
| **Age / maturity** | 2012 — very mature | 2018 — modern | 2019 — modern | 2019 — modern | 2018 — mature | 2019 — modern |
| **Origin** | Spotify | Community | Lyft / Union.ai | Elementl | Netflix | QuantumBlack / McKinsey |

---

## Caching: how each tool decides to skip a task

The most important conceptual difference across the six tools.

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

## Code style: same computation in all six tools

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

Kedro nodes are the most portable — zero framework coupling.  
Metaflow is unique in being class-method based with `self` for state.  
Prefect and Flyte look almost identical — the difference is the runtime.  
Dagster adds observability metadata as a first-class concern.

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

---

## Airflow vs all six

| | Airflow | The six tools |
|---|---|---|
| **Caching** | Not built-in | Built-in — each model differs (see above) |
| **Data passing** | XComs (size-limited, weakly typed) | Native — in-memory, files, or typed artifacts |
| **Local dev** | Full stack (scheduler + webserver + DB) | Python script or lightweight runner |
| **Paradigm** | Task-centric, DAG-as-code | Varies — function, asset, step, node |
| **Operator ecosystem** | Massive (S3, GCS, Snowflake, dbt, …) | Smaller — more DIY |

Airflow dominates on breadth of integrations and team familiarity.  
These tools win on developer experience, built-in caching, and data awareness.
