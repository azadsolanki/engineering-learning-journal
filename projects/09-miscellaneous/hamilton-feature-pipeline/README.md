# Hamilton Feature Engineering Pipeline — POC

Hamilton (by DAGWorks) takes the most unusual approach of any tool in this series: **the DAG is derived entirely from function signatures — no decorators, no explicit wiring**.

## The core idea

```python
# Function NAME  = the artifact it produces
# Function PARAMS = its upstream dependencies

def aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    ...  # Hamilton knows this needs raw_orders() because of the param name

def customer_feature_store(
    aggregation_features: pd.DataFrame,   # ← Hamilton resolves these
    temporal_features: pd.DataFrame,      #   to the functions above
    category_features: pd.DataFrame,
) -> pd.DataFrame:
    ...
```

No `@task`, no `requires()`, no `inputs=`. The graph is the code.

## What this POC covers

| Concept | Where |
|---|---|
| Functions as nodes — name = output, params = inputs | `src/features.py` |
| `Driver.build()` — DAG construction from a module | `src/run.py` |
| `driver.execute(final_vars=[...], inputs={...})` | `src/run.py` |
| Zero framework coupling in node functions | `src/features.py` — no imports from Hamilton |

## Pipeline graph

```
csv_path (input)
    │
raw_orders
    │
    ├──► aggregation_features
    ├──► temporal_features
    └──► category_features
                │
       customer_feature_store  (requested output)
```

Hamilton only runs what's needed to produce `final_vars`. Request a subset and it prunes the graph automatically.

## Caching

Hamilton supports a `ResultStore` that persists outputs and skips recomputation:

```python
from hamilton.plugins import h_cache

dr = (
    driver.Builder()
    .with_modules(features)
    .with_cache(h_cache.SmartCacheAdapter("cache/"))   # persists to disk
    .build()
)
# Second execute() with same inputs → loads from cache/
```

Not configured in this POC (kept minimal), but it's one line to add.

## Quickstart

```bash
cd projects/09-miscellaneous/hamilton-feature-pipeline

# 1. Install
uv pip install -r requirements.txt

# 2. Run
PYTHONPATH=. python src/run.py

# 3. Visualise the DAG (optional)
PYTHONPATH=. python -c "
from hamilton import driver
from src import features
dr = driver.Builder().with_modules(features).build()
dr.display_all_functions('dag.png')
"
```

## Hamilton vs the other tools in this series

| | Hamilton | Luigi | Prefect | Flyte | Dagster | Kedro |
|---|---|---|---|---|---|---|
| **Wiring** | Inferred from function signatures | `requires()` explicit | `@flow` explicit | `@workflow` explicit | Asset graph explicit | `pipeline([node(...)])` explicit |
| **Node definition** | Pure function (zero imports) | Task class | `@task` function | `@task` function | `@asset` function | Pure function (zero imports) |
| **Caching** | Result store (opt-in) | File exists | Hash + TTL | Hash + version | Freshness | File exists |
| **Mental model** | Functions are a DAG | Steps produce files | Functions in a flow | Typed graph | Assets | Nodes wired by name |
| **Best for** | Feature engineering, reusable transformation libraries | Simple batch ETL | General Python flows | ML pipelines | Data observability | ML project standardisation |

Hamilton and Kedro are the two tools where node functions have **zero framework imports** — most portable code of all nine tools.
