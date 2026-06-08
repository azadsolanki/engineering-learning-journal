"""Tasks 2 & 3: Compute features — both are cached so reruns skip recomputation."""
import pandas as pd
import numpy as np
from flytekit import task


# ── Cached: rolling / aggregation features ────────────────────────────────────

@task(cache=True, cache_version="1.0")
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds per-customer aggregate features (expensive group-by work).

    Cached with version "1.0" — Flyte skips this task on reruns if inputs
    hash to the same value. Bump cache_version to invalidate (e.g. "1.1").
    """
    print("[features:agg] Computing customer aggregation features ...")

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

    # Derived ratio features
    agg["spend_per_category"] = agg["total_spend"] / agg["unique_categories"].clip(lower=1)
    agg["order_value_cv"] = agg["std_order_value"] / agg["avg_order_value"].clip(lower=0.01)

    print(f"[features:agg] Done — {len(agg)} customer rows, {len(agg.columns)} columns")
    return agg


# ── Cached: temporal / recency features ───────────────────────────────────────

@task(cache=True, cache_version="1.0")
def compute_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds per-customer time-based features: recency, frequency, tenure.

    Also cached — both this and compute_aggregation_features can run in
    parallel across Flyte workers, then merge_features joins the results.
    """
    print("[features:temporal] Computing temporal features ...")

    df = df.sort_values("order_date")
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

    temporal["days_since_last_order"] = (
        snapshot_date - temporal["last_order_date"]
    ).dt.days

    temporal["customer_tenure_days"] = (
        temporal["last_order_date"] - temporal["first_order_date"]
    ).dt.days.clip(lower=1)

    # Orders per active day (purchase frequency)
    temporal["purchase_frequency"] = (
        temporal["order_count"] / temporal["customer_tenure_days"]
    )

    # Recency bucket: 0–30 days = hot, 31–90 = warm, 90+ = cold
    temporal["recency_bucket"] = pd.cut(
        temporal["days_since_last_order"],
        bins=[-1, 30, 90, float("inf")],
        labels=["hot", "warm", "cold"],
    ).astype(str)

    drop_cols = ["first_order_date", "last_order_date", "order_count"]
    temporal = temporal.drop(columns=drop_cols)

    print(f"[features:temporal] Done — {len(temporal)} rows, {len(temporal.columns)} columns")
    return temporal


# ── Cached: category one-hot encoding ─────────────────────────────────────────

@task(cache=True, cache_version="1.0")
def compute_category_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot preferred category per customer + one-hot encode top categories.
    Cached so the pivot isn't re-run on every pipeline execution.
    """
    print("[features:category] Computing category features ...")

    # Top category per customer
    top_cat = (
        df.groupby(["customer_id", "category"])["order_amount"]
        .sum()
        .reset_index()
        .sort_values("order_amount", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category", "order_amount": "top_category_spend"})
        [["customer_id", "top_category"]]
    )

    # One-hot encode top_category
    dummies = pd.get_dummies(top_cat["top_category"], prefix="cat").astype(int)
    cat_features = pd.concat([top_cat[["customer_id"]], dummies], axis=1)

    print(f"[features:category] Done — {len(cat_features)} rows, {len(cat_features.columns)} columns")
    return cat_features
