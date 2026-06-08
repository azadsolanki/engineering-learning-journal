"""
Tasks 2-4: Compute features — all cached via task_input_hash.

Prefect caching works differently from Flyte:
  - cache_key_fn=task_input_hash  hashes the task inputs at call time
  - cache_expiration sets a TTL on the cached result
  - Results are persisted to a local storage backend (default: ~/.prefect/)
  - Cached results survive across separate flow runs (unlike Flyte local mode)
"""
import pandas as pd
from datetime import timedelta
from prefect import task
from prefect.cache_policies import INPUTS


# ── Cached: aggregation features ──────────────────────────────────────────────

@task(
    name="compute-aggregation-features",
    cache_policy=INPUTS,
    cache_expiration=timedelta(hours=24),
    log_prints=True,
)
def compute_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Per-customer aggregate features. Cached for 24 hours on the same inputs."""
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

    agg["spend_per_category"] = agg["total_spend"] / agg["unique_categories"].clip(lower=1)
    agg["order_value_cv"] = agg["std_order_value"] / agg["avg_order_value"].clip(lower=0.01)

    print(f"[features:agg] Done — {len(agg)} rows, {len(agg.columns)} columns")
    return agg


# ── Cached: temporal features ──────────────────────────────────────────────────

@task(
    name="compute-temporal-features",
    cache_policy=INPUTS,
    cache_expiration=timedelta(hours=24),
    log_prints=True,
)
def compute_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Per-customer recency, frequency, and tenure features. Cached 24 hours."""
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

    temporal["purchase_frequency"] = (
        temporal["order_count"] / temporal["customer_tenure_days"]
    )

    temporal["recency_bucket"] = pd.cut(
        temporal["days_since_last_order"],
        bins=[-1, 30, 90, float("inf")],
        labels=["hot", "warm", "cold"],
    ).astype(str)

    temporal = temporal.drop(columns=["first_order_date", "last_order_date", "order_count"])

    print(f"[features:temporal] Done — {len(temporal)} rows, {len(temporal.columns)} columns")
    return temporal


# ── Cached: category features ──────────────────────────────────────────────────

@task(
    name="compute-category-features",
    cache_policy=INPUTS,
    cache_expiration=timedelta(hours=24),
    log_prints=True,
)
def compute_category_features(df: pd.DataFrame) -> pd.DataFrame:
    """Top category per customer + one-hot encoding. Cached 24 hours."""
    print("[features:category] Computing category features ...")

    top_cat = (
        df.groupby(["customer_id", "category"])["order_amount"]
        .sum()
        .reset_index()
        .sort_values("order_amount", ascending=False)
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})
        [["customer_id", "top_category"]]
    )

    dummies = pd.get_dummies(top_cat["top_category"], prefix="cat").astype(int)
    cat_features = pd.concat([top_cat[["customer_id"]], dummies], axis=1)

    print(f"[features:category] Done — {len(cat_features)} rows, {len(cat_features.columns)} columns")
    return cat_features
