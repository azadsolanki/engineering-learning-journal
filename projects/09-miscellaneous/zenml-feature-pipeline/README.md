# ZenML Feature Engineering Pipeline — POC

ZenML sits between Prefect (lightweight) and Flyte (heavy) — it uses the same `@step` + `@pipeline` pattern but adds the **Stack** concept: a pluggable set of infrastructure components (orchestrator, artifact store, container registry) that the pipeline runs on.

## What this POC covers

| Concept | Where |
|---|---|
| `@step(enable_cache=True/False)` | `src/pipeline.py` — feature steps cached, ingest not |
| `@pipeline(enable_cache=True)` | `src/pipeline.py` |
| Local stack — zero-infra execution | Runs out of the box, no config needed |
| Artifact store — automatic output persistence | ZenML stores step outputs in `~/.zenml/` |

## Pipeline

```
ingest_raw_data  (enable_cache=False)
        │
        ├──► compute_aggregation_features  (cached)
        ├──► compute_temporal_features     (cached)
        └──► compute_category_features     (cached)
                        │
                  merge_and_save
```

## Caching

ZenML caches by **input hash**, same as Prefect — and it works locally out of the box with no extra config. Artifacts are stored in `~/.zenml/`.

```python
@step(enable_cache=True)   # skip if inputs unchanged
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    ...

@step(enable_cache=False)  # always rerun (I/O, non-deterministic)
def ingest_raw_data(csv_path: str) -> pd.DataFrame:
    ...
```

Run twice — on the second run the three feature steps log `Using cached artifact` and return immediately.

## The Stack concept

The Stack is ZenML's key differentiator. Switch infrastructure without changing pipeline code:

```bash
# Local (default — what this POC uses)
zenml stack set default

# Switch to a cloud stack
zenml stack register gcp-stack \
    -o vertex-orchestrator \
    -a gcs-artifact-store
zenml stack set gcp-stack
python src/pipeline.py   # same code, runs on Vertex AI
```

## Quickstart

```bash
cd projects/09-miscellaneous/zenml-feature-pipeline

# 1. Install
uv pip install -r requirements.txt

# 2. Run
PYTHONPATH=. python src/pipeline.py

# 3. Run again — feature steps show "Using cached artifact"
PYTHONPATH=. python src/pipeline.py

# 4. View run history
zenml pipeline runs list

# 5. Open dashboard (optional)
zenml login --local   # → http://localhost:8237
```

## ZenML vs the other tools in this series

| | ZenML | Prefect | Flyte | Dagster | Metaflow |
|---|---|---|---|---|---|
| **Caching** | Hash-based, works locally | Hash + TTL, works locally | Hash + version, needs cluster | Freshness/lineage | Step checkpoint (failure resume) |
| **Stack abstraction** | Yes — swap infra via CLI | No | Yes — Flyte cluster | Partial | Yes — `@kubernetes`, `@batch` |
| **Local dev** | Zero infra | Zero infra | Zero infra | Zero infra | Zero infra |
| **ML focus** | Strong — integrates MLflow, Feast, etc. | General-purpose | Strong | Data-asset focus | Strong |
| **Learning curve** | Low-medium | Low | Steeper | Medium | Low-medium |

ZenML is the closest thing to "Flyte but easier to run locally" — same caching model, same decorator style, but the Stack makes infrastructure swappable without touching pipeline code.
