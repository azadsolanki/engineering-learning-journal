"""
Prefect Feature Engineering Pipeline
======================================
Demonstrates:
  - @task with cache_policy=INPUTS + cache_expiration for expensive feature tasks
  - Parallel task submission via .submit() + futures (ConcurrentTaskRunner)
  - @flow composition with typed Python — no YAML, no DAG classes
  - Caching that actually persists across separate flow runs (unlike Flyte local)

Run:
    python src/flow.py
    python src/flow.py --csv data/orders.csv

Or via Prefect CLI:
    prefect flow run src/flow.py:feature_pipeline
"""
import sys
from pathlib import Path
from prefect import flow
from prefect.task_runners import ThreadPoolTaskRunner

from src.tasks.ingest import ingest_raw_data
from src.tasks.features import (
    compute_aggregation_features,
    compute_temporal_features,
    compute_category_features,
)
from src.tasks.output import merge_features, save_feature_store


@flow(
    name="feature-engineering-pipeline",
    task_runner=ThreadPoolTaskRunner(max_workers=3),
    log_prints=True,
)
def feature_pipeline(csv_path: str = "data/orders.csv") -> str:
    """
    End-to-end feature engineering flow.

    DAG shape:
        ingest_raw_data
            ├── compute_aggregation_features  (cached, parallel)
            ├── compute_temporal_features     (cached, parallel)
            └── compute_category_features     (cached, parallel)
                        ↓
                  merge_features
                        ↓
                 save_feature_store  →  str (output dir path)

    The three feature tasks are submitted concurrently via .submit().
    Prefect resolves futures automatically when passed to downstream tasks.
    """
    raw = ingest_raw_data(csv_path=csv_path)

    # .submit() dispatches to ThreadPoolTaskRunner — all three run concurrently.
    # Each is cached: same DataFrame hash → skip task body, return stored result.
    agg_future = compute_aggregation_features.submit(df=raw)
    temporal_future = compute_temporal_features.submit(df=raw)
    category_future = compute_category_features.submit(df=raw)

    # Prefect resolves futures when they are passed as arguments
    merged = merge_features(
        agg_features=agg_future,
        temporal_features=temporal_future,
        category_features=category_future,
    )

    return save_feature_store(features=merged)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/orders.csv")
    args = parser.parse_args()

    result = feature_pipeline(csv_path=args.csv)
    print(f"\nFeature store → {result}")
