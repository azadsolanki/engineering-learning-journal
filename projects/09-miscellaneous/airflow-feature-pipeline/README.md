# Airflow Feature Engineering Pipeline — POC

The reference tool — all other POCs in this series compare against Airflow.
Built with the **TaskFlow API** (Airflow 2.x).

## What this POC covers

| Concept | Where |
|---|---|
| `@dag` + `@task` — TaskFlow API | `src/dag.py` |
| Automatic XCom via return values | All tasks — no `xcom_push/pull` needed |
| Implicit edges from argument wiring | `merge_features(agg, temporal, category)` |
| `retries` + `retry_delay` in `default_args` | `@dag(default_args=...)` |

## Pipeline DAG

```
ingest_raw_data
        │
        ├──► compute_agg_features
        ├──► compute_temporal_features
        └──► compute_category_features
                        │
                  merge_features
                        │
               save_feature_store
```

Airflow infers edges from how tasks are called — no `>>` operators needed with TaskFlow API.

## Caching

**Airflow has no built-in task caching.** This is the key gap vs every other tool in this series.

Common workarounds:
```python
# Option 1: skip logic inside the task
@task()
def compute_agg_features(raw_path: str) -> str:
    if Path("output/agg.parquet").exists():
        return "output/agg.parquet"   # manual short-circuit
    # ... compute ...

# Option 2: ShortCircuitOperator upstream of expensive tasks
```

## XCom and data passing

TaskFlow wraps XComs automatically — return a value, it's stored; declare it as a parameter, it's injected. **Limitation:** XComs live in the Airflow metadata DB — not suited for large DataFrames. This POC passes file paths via XCom and reads DataFrames from disk, which is the standard workaround.

## Quickstart

```bash
cd projects/09-miscellaneous/airflow-feature-pipeline

# 1. Install
uv pip install -r requirements.txt

# 2. Init DB and create user
export AIRFLOW_HOME=$(pwd)/.airflow
airflow db migrate
airflow users create --username admin --password admin \
    --firstname A --lastname B --role Admin --email admin@example.com

# 3. Start (scheduler + webserver)
mkdir -p .airflow/dags && cp src/dag.py .airflow/dags/
airflow standalone   # → http://localhost:8080

# 4. Trigger
airflow dags trigger feature_pipeline

# 5. Verify DAG parses (no scheduler needed)
python -c "from src.dag import feature_pipeline_dag; print(feature_pipeline_dag.dag_id)"
```

## Airflow vs the other tools in this series

| | Airflow | Prefect | Flyte | ZenML | Hamilton | Luigi | Kedro |
|---|---|---|---|---|---|---|---|
| **Caching** | None built-in | Hash + TTL | Hash + version | Hash (local) | Result store | File exists | File exists |
| **Data passing** | XCom (DB, size-limited) | Return values | Typed return values | Return values | Return values | Files | DataCatalog |
| **Local dev** | Full stack required | Zero infra | Zero infra | Zero infra | Zero infra | Zero infra | Zero infra |
| **Ecosystem** | Massive — biggest operator library | Growing | ML-focused | ML stack | Micro-framework | Small, stable | ML + data |

Airflow wins on ecosystem breadth and team familiarity. Every other tool in this series beats it on local dev experience and built-in caching.
