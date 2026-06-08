# Dagster Feature Engineering Pipeline — POC

Same pipeline as the [Flyte](../flyte-feature-pipeline/) and [Prefect](../prefect-feature-pipeline/) POCs — built with Dagster's **Software-Defined Assets** model.

## What this POC covers

| Concept | Where |
|---|---|
| `@asset` — asset-centric (not task-centric) model | `src/assets/features.py` |
| `AssetIn` for explicit upstream wiring | Same — all feature assets declare `ins=` |
| `group_name` for logical grouping in the UI | Same — `ingestion`, `features`, `output` |
| `Output` + `MetadataValue` for observable metadata | `customer_feature_store` asset |
| `materialize()` for local execution (no server) | `scripts/run_local.py` |
| `Definitions` + `define_asset_job` for registration | `src/definitions.py` |

## Pipeline asset graph

```
raw_orders  (ingestion group)
        │
        ├──► aggregation_features  ──┐  (features group)
        ├──► temporal_features     ──┤
        └──► category_features    ──┘
                        │
               customer_feature_store   (output group)
```

## Caching in Dagster

Dagster's caching model is **asset-freshness based**, not input-hash based.

- Each asset is a persistent artifact tracked in the asset catalog
- Dagster tracks _when_ each asset was last materialised and compares it to upstream assets
- If an upstream asset hasn't changed since the downstream was last materialised → downstream is considered **fresh** and can be skipped
- Configured via `AutoMaterializePolicy` or `FreshnessPolicy` on each asset

```python
from dagster import AutoMaterializePolicy, FreshnessPolicy

@asset(
    auto_materialize_policy=AutoMaterializePolicy.eager(),    # re-run when upstream changes
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60), # alert if stale > 1hr
)
def aggregation_features(...): ...
```

This is different from Prefect/Flyte which hash inputs — Dagster reasons about **lineage and time**, which fits the data asset mental model better.

## Quickstart

```bash
cd projects/09-miscellaneous/dagster-feature-pipeline

# 1. Install deps
uv pip install -r requirements.txt

# 2. Run pipeline locally (no server needed)
PYTHONPATH=. python scripts/run_local.py

# 3. (Optional) Explore in the Dagster UI
PYTHONPATH=. dagster dev -f src/definitions.py
# open http://localhost:3000 → Asset Catalog → Materialise All
```

## Project structure

```
dagster-feature-pipeline/
├── data/
│   └── orders.csv                  ← same synthetic dataset as other POCs
├── scripts/
│   └── run_local.py                ← materialize() entrypoint
├── src/
│   ├── assets/
│   │   └── features.py             ← all @asset definitions
│   └── definitions.py              ← Definitions + job registration
└── requirements.txt
```

## Dagster vs Airflow

| | Dagster | Airflow |
|---|---|---|
| **Unit of work** | `@asset` — a data artifact | `Operator` — a computation step |
| **Mental model** | Asset-centric: what data exists | Task-centric: what runs |
| **Caching** | Freshness policies + asset catalog | Not built-in |
| **Observability** | Built-in — metadata, lineage, data versions | Requires plugins |
| **Local dev** | `materialize()` — no scheduler | Full Airflow stack |
| **UI** | Rich asset catalog + lineage graph | Task-focused DAG view |
| **Maturity** | Modern, fast-growing | Battle-tested, huge ecosystem |

## Dagster vs Flyte / Prefect (same pipeline)

| | Dagster | Flyte | Prefect |
|---|---|---|---|
| **Abstraction** | Asset (data artifact) | Task (function) | Task (function) |
| **Caching key** | Lineage + time (freshness) | Input hash | Input hash + TTL |
| **Local caching** | Asset catalog (ephemeral in `materialize()`) | Metadata only | Persists to `~/.prefect/` |
| **Best for** | Data-asset workflows, observability | ML pipelines, strong typing | General Python flows, simplicity |
| **Learning curve** | Steeper — new mental model | Steeper — Flyte concepts | Low — feels like Python |
