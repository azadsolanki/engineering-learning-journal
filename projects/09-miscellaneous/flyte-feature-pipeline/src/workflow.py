"""
Flyte Feature Engineering Pipeline
===================================
Demonstrates:
  - @task with cache=True / cache_version for expensive feature tasks
  - Typed I/O: FlyteFile in, pd.DataFrame between tasks, FlyteDirectory out
  - Parallel task execution (agg + temporal + category run concurrently)
  - @workflow composition

Run locally:
    pyflyte run src/workflow.py feature_pipeline \
        --csv_path data/orders.csv

Or as plain Python (no Flyte cluster needed):
    python -c "
    from flytekit import FlyteFile
    from src.workflow import feature_pipeline
    result = feature_pipeline(csv_path=FlyteFile('data/orders.csv'))
    print('Output dir:', result)
    "
"""
from flytekit import workflow, FlyteFile, FlyteDirectory

from src.tasks.ingest import ingest_raw_data
from src.tasks.features import (
    compute_aggregation_features,
    compute_temporal_features,
    compute_category_features,
)
from src.tasks.output import merge_features, save_feature_store


@workflow
def feature_pipeline(csv_path: FlyteFile) -> FlyteDirectory:
    """
    End-to-end feature engineering pipeline.

    DAG shape:
        ingest_raw_data
            ├── compute_aggregation_features  (cached)
            ├── compute_temporal_features     (cached)
            └── compute_category_features     (cached)
                        ↓
                  merge_features
                        ↓
                 save_feature_store  →  FlyteDirectory (artifact)
    """
    raw = ingest_raw_data(csv_path=csv_path)

    # These three tasks are independent — Flyte schedules them in parallel.
    # Each is cached: on rerun with the same input hash they are skipped.
    agg = compute_aggregation_features(df=raw)
    temporal = compute_temporal_features(df=raw)
    category = compute_category_features(df=raw)

    merged = merge_features(
        agg_features=agg,
        temporal_features=temporal,
        category_features=category,
    )

    return save_feature_store(features=merged)
