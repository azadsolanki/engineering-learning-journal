"""
Hamilton Feature Engineering Pipeline
=======================================
Hamilton's core idea: the DAG is derived entirely from function signatures.
  - Function NAME   = the name of the data artifact it produces
  - Function PARAMS = the names of its upstream dependencies
  - No @dag, no @workflow, no explicit wiring — just plain functions

Hamilton matches parameter names to function names to build the graph.
Ask for "customer_feature_store" and Hamilton figures out everything
needed to produce it by walking the dependency graph backwards.

Caching: Hamilton supports result stores (ResultStore) that persist
outputs to disk/S3 and skip recomputation when results already exist.
The local ResultStore checks a directory for prior results.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


# ── Each function IS a node. Name = output. Params = inputs. ──────────────────

def raw_orders(csv_path: str) -> pd.DataFrame:
    """Hamilton finds this because downstream nodes declare `raw_orders` as a param."""
    df = pd.read_csv(csv_path, parse_dates=["order_date"])
    df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
    df["order_amount"] = df["order_amount"].clip(lower=0)
    print(f"[raw_orders] {len(df)} rows, {df['customer_id'].nunique()} customers")
    return df


def aggregation_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Hamilton resolves `raw_orders` param → calls raw_orders() above.
    No import, no explicit dependency declaration needed.
    """
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
    print(f"[aggregation_features] {len(agg)} rows, {len(agg.columns)} cols")
    return agg


def temporal_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    df = raw_orders.sort_values("order_date")
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
    print(f"[temporal_features] {len(t)} rows, {len(t.columns)} cols")
    return t


def category_features(raw_orders: pd.DataFrame) -> pd.DataFrame:
    top = (
        raw_orders.groupby(["customer_id", "category"])["order_amount"].sum().reset_index()
        .sort_values("order_amount", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})[["customer_id", "top_category"]]
    )
    dummies = pd.get_dummies(top["top_category"], prefix="cat").astype(int)
    result = pd.concat([top[["customer_id"]], dummies], axis=1)
    print(f"[category_features] {len(result)} rows, {len(result.columns)} cols")
    return result


def customer_feature_store(
    aggregation_features: pd.DataFrame,
    temporal_features: pd.DataFrame,
    category_features: pd.DataFrame,
) -> pd.DataFrame:
    """
    Terminal node. Hamilton fans in all three feature tables.
    Parameter names match the function names above — no explicit wiring.
    """
    merged = (
        aggregation_features
        .merge(temporal_features, on="customer_id", how="inner")
        .merge(category_features, on="customer_id", how="left")
    )
    cat_cols = [c for c in merged.columns if c.startswith("cat_")]
    merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)
    num_cols = [c for c in merged.select_dtypes(include=[np.number]).columns if c != "customer_id"]
    merged[num_cols] = StandardScaler().fit_transform(merged[num_cols])
    print(f"[customer_feature_store] {merged.shape[0]} customers × {merged.shape[1]} features")
    return merged
