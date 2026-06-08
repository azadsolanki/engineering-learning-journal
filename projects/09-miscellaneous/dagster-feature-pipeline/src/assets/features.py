"""
Software-Defined Assets for the feature engineering pipeline.

Dagster's model is asset-centric, not task-centric:
  - Each @asset represents a persistent data artifact (not a computation step)
  - Caching is handled by the IO manager — if an asset is already materialized
    and "fresh" (per freshness policy), Dagster skips re-computation
  - Assets are the unit of observability in the Dagster UI

Key concepts shown here:
  - @asset with deps= for explicit lineage
  - AssetIn for typed upstream wiring
  - group_name for logical grouping in the UI
  - Metadata emitted via context.add_output_metadata()
"""
import numpy as np
import pandas as pd
from dagster import asset, AssetIn, Output, MetadataValue
from sklearn.preprocessing import StandardScaler


@asset(
    name="raw_orders",
    group_name="ingestion",
    description="Validated raw orders loaded from CSV.",
)
def raw_orders(context) -> pd.DataFrame:
    csv_path = context.op_config.get("csv_path", "data/orders.csv")
    df = pd.read_csv(csv_path, parse_dates=["order_date"])
    df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
    df["order_amount"] = df["order_amount"].clip(lower=0)

    context.add_output_metadata({
        "row_count": MetadataValue.int(len(df)),
        "unique_customers": MetadataValue.int(df["customer_id"].nunique()),
        "columns": MetadataValue.text(", ".join(df.columns)),
    })
    return df


# ── Feature assets — all downstream of raw_orders ─────────────────────────────

@asset(
    name="aggregation_features",
    ins={"raw_orders": AssetIn()},
    group_name="features",
    description="Per-customer spend and order aggregations.",
)
def aggregation_features(context, raw_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Per-customer aggregate features.

    Caching: Dagster tracks the asset's last materialization time and the
    upstream asset's last materialization time. If raw_orders hasn't changed
    since this asset was last computed, Dagster can skip re-materialization
    (configured via freshness policies or auto-materialization policies).
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

    context.add_output_metadata({"row_count": MetadataValue.int(len(agg))})
    return agg


@asset(
    name="temporal_features",
    ins={"raw_orders": AssetIn()},
    group_name="features",
    description="Per-customer recency, frequency, and tenure features.",
)
def temporal_features(context, raw_orders: pd.DataFrame) -> pd.DataFrame:
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

    context.add_output_metadata({"row_count": MetadataValue.int(len(temporal))})
    return temporal


@asset(
    name="category_features",
    ins={"raw_orders": AssetIn()},
    group_name="features",
    description="Top category per customer with one-hot encoding.",
)
def category_features(context, raw_orders: pd.DataFrame) -> pd.DataFrame:
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

    context.add_output_metadata({"row_count": MetadataValue.int(len(result))})
    return result


# ── Merge + output ─────────────────────────────────────────────────────────────

@asset(
    name="customer_feature_store",
    ins={
        "aggregation_features": AssetIn(),
        "temporal_features": AssetIn(),
        "category_features": AssetIn(),
    },
    group_name="output",
    description="Merged, normalised feature table — the final feature store artifact.",
)
def customer_feature_store(
    context,
    aggregation_features: pd.DataFrame,
    temporal_features: pd.DataFrame,
    category_features: pd.DataFrame,
) -> Output[pd.DataFrame]:
    merged = (
        aggregation_features
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

    return Output(
        value=merged,
        metadata={
            "customers": MetadataValue.int(len(merged)),
            "features": MetadataValue.int(len(merged.columns)),
            "columns": MetadataValue.text(", ".join(merged.columns)),
        },
    )
