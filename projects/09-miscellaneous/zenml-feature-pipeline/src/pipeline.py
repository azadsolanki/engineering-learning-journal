"""
ZenML Feature Engineering Pipeline
=====================================
ZenML uses @step + @pipeline decorators, similar to Flyte/Prefect, but
adds the concept of a Stack — the pluggable set of infrastructure components
(artifact store, orchestrator, container registry) that the pipeline runs on.

Key concepts shown:
  - @step — individual pipeline step with typed I/O
  - @pipeline — flow that wires steps together
  - Artifact store — ZenML persists step outputs automatically (caching)
  - Local stack — zero-infra local execution

Caching: ZenML caches step outputs in the artifact store by default.
  Same inputs (by hash) → step is skipped, cached artifact returned.
  Identical to Flyte/Prefect's input-hash model, but works locally
  without any extra configuration.
  Disable per-step: @step(enable_cache=False)
  Disable pipeline-wide: @pipeline(enable_cache=False)

Run:
    python src/pipeline.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from zenml import step, pipeline
from zenml.config import DockerSettings


# ── Steps ─────────────────────────────────────────────────────────────────────

@step(enable_cache=False)
def ingest_raw_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["order_date"])
    df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
    df["order_amount"] = df["order_amount"].clip(lower=0)
    print(f"[ingest] {len(df)} rows, {df['customer_id'].nunique()} customers")
    return df


@step(enable_cache=True)
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cached — same DataFrame hash → ZenML returns prior artifact."""
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
    return agg


@step(enable_cache=True)
def compute_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cached."""
    df = df.sort_values("order_date")
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
    return t


@step(enable_cache=True)
def compute_category_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cached."""
    top = (
        df.groupby(["customer_id", "category"])["order_amount"].sum().reset_index()
        .sort_values("order_amount", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})[["customer_id", "top_category"]]
    )
    dummies = pd.get_dummies(top["top_category"], prefix="cat").astype(int)
    result = pd.concat([top[["customer_id"]], dummies], axis=1)
    print(f"[category] {len(result)} rows, {len(result.columns)} cols")
    return result


@step
def merge_and_save(
    agg: pd.DataFrame,
    temporal: pd.DataFrame,
    category: pd.DataFrame,
) -> str:
    import os, tempfile
    merged = (
        agg.merge(temporal, on="customer_id", how="inner")
           .merge(category, on="customer_id", how="left")
    )
    cat_cols = [c for c in merged.columns if c.startswith("cat_")]
    merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)
    num_cols = [c for c in merged.select_dtypes(include=[np.number]).columns if c != "customer_id"]
    merged[num_cols] = StandardScaler().fit_transform(merged[num_cols])

    out_dir = tempfile.mkdtemp(prefix="zenml_feature_store_")
    out = Path(out_dir) / "customer_features.parquet"
    merged.to_parquet(out, index=False)
    print(f"[output] {out}  ({os.path.getsize(out):,} bytes)")
    print(f"         {len(merged)} customers × {len(merged.columns)} features")
    return out_dir


# ── Pipeline ───────────────────────────────────────────────────────────────────

@pipeline(name="feature-engineering-pipeline", enable_cache=True)
def feature_pipeline(csv_path: str = "data/orders.csv"):
    """
    ZenML pipeline — steps run sequentially on the local stack by default.
    Cached steps (enable_cache=True) are skipped on rerun if inputs unchanged.
    Switch to a cloud stack to run on Vertex AI, SageMaker, etc. with no code changes.
    """
    raw = ingest_raw_data(csv_path=csv_path)
    agg = compute_aggregation_features(df=raw)
    temporal = compute_temporal_features(df=raw)
    category = compute_category_features(df=raw)
    merge_and_save(agg=agg, temporal=temporal, category=category)


if __name__ == "__main__":
    feature_pipeline()
