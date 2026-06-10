"""
Airflow Feature Engineering Pipeline — TaskFlow API (Airflow 2.x)
===================================================================
The TaskFlow API (@task decorator, added in Airflow 2.0) eliminates the
need for explicit XCom push/pull. Return values are automatically stored
as XComs and injected as arguments into downstream tasks.

Key concepts shown:
  - @dag + @task  —  modern DAG definition (no more DAG context managers)
  - XCom via return values  —  automatic, no xcom_push/pull boilerplate
  - task_id, retries, retry_delay  —  task-level config
  - Implicit dependency from argument wiring

Caching: Airflow has NO built-in task-level caching.
  Common workarounds: ShortCircuitOperator, skip logic inside run(),
  or external idempotency (check if output exists before computing).

Run locally:
    # One-time setup
    export AIRFLOW_HOME=$(pwd)/.airflow
    airflow db migrate
    airflow users create --username admin --password admin \
        --firstname A --lastname B --role Admin --email a@b.com

    # Copy this file to the dags folder
    cp src/dag.py .airflow/dags/

    # Start scheduler + webserver
    airflow standalone
    # open http://localhost:8080, trigger the DAG

    # Or run a single task without the scheduler
    airflow tasks test feature_pipeline ingest_raw_data 2024-01-01
"""
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from airflow.sdk import dag, task
from sklearn.preprocessing import StandardScaler


@dag(
    dag_id="feature_pipeline",
    schedule=None,          # manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["feature-engineering", "poc"],
)
def feature_pipeline():
    """
    End-to-end feature engineering pipeline using the TaskFlow API.

    DAG shape:
        ingest_raw_data
            ├── compute_agg_features
            ├── compute_temporal_features
            └── compute_category_features
                        ↓
                  merge_features
                        ↓
                 save_feature_store
    """

    @task()
    def ingest_raw_data(csv_path: str = "data/orders.csv") -> str:
        """Load, validate, and serialise raw orders. Returns tmp parquet path."""
        df = pd.read_csv(csv_path, parse_dates=["order_date"])
        df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
        df["order_amount"] = df["order_amount"].clip(lower=0)
        print(f"[ingest] {len(df)} rows, {df['customer_id'].nunique()} customers")
        # XComs can't carry DataFrames directly — serialise to a tmp file
        path = tempfile.mktemp(suffix=".parquet", prefix="af_raw_")
        df.to_parquet(path, index=False)
        return path  # returned value auto-pushed as XCom

    @task()
    def compute_agg_features(raw_path: str) -> str:
        df = pd.read_parquet(raw_path)
        agg = (
            df.groupby("customer_id")
            .agg(
                total_orders=("order_id", "count"),
                total_spend=("order_amount", "sum"),
                avg_order_value=("order_amount", "mean"),
                std_order_value=("order_amount", "std"),
                max_order_value=("order_amount", "max"),
                min_order_value=("order_amount", "min"),
                return_rate=("returned", "mean"),
                avg_discount=("discount_pct", "mean"),
                unique_categories=("category", "nunique"),
            )
            .reset_index()
        )
        agg["spend_per_category"] = agg["total_spend"] / agg["unique_categories"].clip(lower=1)
        agg["order_value_cv"] = agg["std_order_value"] / agg["avg_order_value"].clip(lower=0.01)
        print(f"[agg] {len(agg)} rows, {len(agg.columns)} cols")
        path = tempfile.mktemp(suffix=".parquet", prefix="af_agg_")
        agg.to_parquet(path, index=False)
        return path

    @task()
    def compute_temporal_features(raw_path: str) -> str:
        df = pd.read_parquet(raw_path).sort_values("order_date")
        snapshot = df["order_date"].max()
        t = (
            df.groupby("customer_id")
            .agg(first=("order_date", "min"), last=("order_date", "max"), n=("order_id", "count"))
            .reset_index()
        )
        t["days_since_last_order"] = (snapshot - t["last"]).dt.days
        t["customer_tenure_days"] = (t["last"] - t["first"]).dt.days.clip(lower=1)
        t["purchase_frequency"] = t["n"] / t["customer_tenure_days"]
        t["recency_bucket"] = pd.cut(
            t["days_since_last_order"], bins=[-1, 30, 90, float("inf")],
            labels=["hot", "warm", "cold"],
        ).astype(str)
        t = t.drop(columns=["first", "last", "n"])
        print(f"[temporal] {len(t)} rows, {len(t.columns)} cols")
        path = tempfile.mktemp(suffix=".parquet", prefix="af_tmp_")
        t.to_parquet(path, index=False)
        return path

    @task()
    def compute_category_features(raw_path: str) -> str:
        df = pd.read_parquet(raw_path)
        top = (
            df.groupby(["customer_id", "category"])["order_amount"].sum().reset_index()
            .sort_values("order_amount", ascending=False)
            .drop_duplicates("customer_id")
            .rename(columns={"category": "top_category"})[["customer_id", "top_category"]]
        )
        dummies = pd.get_dummies(top["top_category"], prefix="cat").astype(int)
        result = pd.concat([top[["customer_id"]], dummies], axis=1)
        print(f"[category] {len(result)} rows, {len(result.columns)} cols")
        path = tempfile.mktemp(suffix=".parquet", prefix="af_cat_")
        result.to_parquet(path, index=False)
        return path

    @task()
    def merge_features(agg_path: str, temporal_path: str, category_path: str) -> str:
        agg = pd.read_parquet(agg_path)
        temporal = pd.read_parquet(temporal_path)
        category = pd.read_parquet(category_path)
        merged = agg.merge(temporal, on="customer_id").merge(category, on="customer_id", how="left")
        cat_cols = [c for c in merged.columns if c.startswith("cat_")]
        merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)
        num_cols = [c for c in merged.select_dtypes(include=[np.number]).columns if c != "customer_id"]
        merged[num_cols] = StandardScaler().fit_transform(merged[num_cols])
        print(f"[merge] {merged.shape[0]} customers × {merged.shape[1]} features")
        path = tempfile.mktemp(suffix=".parquet", prefix="af_merged_")
        merged.to_parquet(path, index=False)
        return path

    @task()
    def save_feature_store(merged_path: str) -> str:
        import os
        df = pd.read_parquet(merged_path)
        out_dir = tempfile.mkdtemp(prefix="airflow_feature_store_")
        out = Path(out_dir) / "customer_features.parquet"
        df.to_parquet(out, index=False)
        print(f"[output] {out}  ({os.path.getsize(out):,} bytes)")
        print(f"         {len(df)} customers × {len(df.columns)} features")
        return out_dir

    # Wire the DAG — Airflow infers edges from argument passing
    raw = ingest_raw_data()
    agg = compute_agg_features(raw)
    temporal = compute_temporal_features(raw)
    category = compute_category_features(raw)
    merged = merge_features(agg, temporal, category)
    save_feature_store(merged)


# Instantiate the DAG — Airflow discovers this at module level
feature_pipeline_dag = feature_pipeline()
