"""
Kedro nodes for the feature engineering pipeline.

In Kedro, nodes are plain Python functions — no decorators, no base classes.
The framework wires them together via the DataCatalog and Pipeline definition.

Caching in Kedro:
  - Each node's output is a named dataset defined in catalog.yml
  - If that dataset's file already exists on disk, Kedro loads it instead
    of re-running the node — identical to Luigi's LocalTarget approach
  - Delete the file to force recomputation
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def ingest_raw_data(orders_csv: pd.DataFrame) -> pd.DataFrame:
    df = orders_csv.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
    df["order_amount"] = df["order_amount"].clip(lower=0)
    print(f"[ingest] {len(df)} rows, {df['customer_id'].nunique()} customers")
    return df


def compute_aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    agg = (
        raw_orders.groupby("customer_id")
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
    print(f"[agg] {len(agg)} rows, {len(agg.columns)} columns")
    return agg


def compute_temporal_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    df = raw_orders.sort_values("order_date")
    snapshot_date = df["order_date"].max()
    temporal = (
        df.groupby("customer_id")
        .agg(
            first_order_date=("order_date", "min"),
            last_order_date=("order_date", "max"),
            order_count=("order_id", "count"),
        )
        .reset_index()
    )
    temporal["days_since_last_order"] = (snapshot_date - temporal["last_order_date"]).dt.days
    temporal["customer_tenure_days"] = (
        temporal["last_order_date"] - temporal["first_order_date"]
    ).dt.days.clip(lower=1)
    temporal["purchase_frequency"] = temporal["order_count"] / temporal["customer_tenure_days"]
    temporal["recency_bucket"] = pd.cut(
        temporal["days_since_last_order"],
        bins=[-1, 30, 90, float("inf")],
        labels=["hot", "warm", "cold"],
    ).astype(str)
    temporal = temporal.drop(columns=["first_order_date", "last_order_date", "order_count"])
    print(f"[temporal] {len(temporal)} rows, {len(temporal.columns)} columns")
    return temporal


def compute_category_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    top_cat = (
        raw_orders.groupby(["customer_id", "category"])["order_amount"]
        .sum()
        .reset_index()
        .sort_values("order_amount", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})
        [["customer_id", "top_category"]]
    )
    dummies = pd.get_dummies(top_cat["top_category"], prefix="cat").astype(int)
    result = pd.concat([top_cat[["customer_id"]], dummies], axis=1)
    print(f"[category] {len(result)} rows, {len(result.columns)} columns")
    return result


def merge_features(
    agg_features: pd.DataFrame,
    temporal_features: pd.DataFrame,
    category_features: pd.DataFrame,
) -> pd.DataFrame:
    merged = (
        agg_features
        .merge(temporal_features, on="customer_id", how="inner")
        .merge(category_features, on="customer_id", how="left")
    )
    cat_cols = [c for c in merged.columns if c.startswith("cat_")]
    merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)

    numeric_cols = [
        c for c in merged.select_dtypes(include=[np.number]).columns
        if c != "customer_id"
    ]
    merged[numeric_cols] = StandardScaler().fit_transform(merged[numeric_cols])
    print(f"[merge] {merged.shape[0]} customers × {merged.shape[1]} features")
    return merged
