"""
Metaflow Feature Engineering Pipeline
========================================
Metaflow's model is step-based inside a FlowSpec class:
  - Each method decorated with @step is a pipeline stage
  - self.next() declares transitions — including fan-out (parallel branches)
  - Data is passed via self.attribute — Metaflow serialises it automatically
  - self.next(a, b, c) fans out; a join step receives `inputs` to merge them

Caching / resume:
  - Every step's outputs are persisted as artifacts in ~/.metaflow/
  - `python flow.py resume` re-runs only failed/changed steps, reusing
    prior step artifacts for everything that already succeeded
  - This is Metaflow's equivalent of caching: step-level checkpointing

Run:
    python src/flow.py run
    python src/flow.py run --csv_path data/orders.csv

Resume a failed run:
    python src/flow.py resume

Show past runs:
    python src/flow.py show
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from metaflow import FlowSpec, Parameter, step
from sklearn.preprocessing import StandardScaler


class FeaturePipeline(FlowSpec):

    csv_path = Parameter("csv_path", default="data/orders.csv", help="Path to input CSV")

    # ── Step 1: ingest ─────────────────────────────────────────────────────────

    @step
    def start(self):
        """Load and validate raw orders CSV."""
        df = pd.read_csv(self.csv_path, parse_dates=["order_date"])
        df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
        df["order_amount"] = df["order_amount"].clip(lower=0)

        self.raw = df
        print(f"[start] {len(df)} rows, {df['customer_id'].nunique()} customers")

        # Fan out: all three feature steps run in parallel
        self.next(self.agg_features, self.temporal_features, self.category_features)

    # ── Steps 2-4: parallel feature computation ────────────────────────────────

    @step
    def agg_features(self):
        """Per-customer spend and order aggregations."""
        df = self.raw
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
        self.result = agg
        print(f"[agg] {len(agg)} rows, {len(agg.columns)} columns")
        self.next(self.join_features)

    @step
    def temporal_features(self):
        """Per-customer recency, frequency, tenure."""
        df = self.raw.sort_values("order_date")
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
        self.result = temporal
        print(f"[temporal] {len(temporal)} rows, {len(temporal.columns)} columns")
        self.next(self.join_features)

    @step
    def category_features(self):
        """Top category per customer + one-hot encoding."""
        df = self.raw
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
        self.result = pd.concat([top_cat[["customer_id"]], dummies], axis=1)
        print(f"[category] {len(self.result)} rows, {len(self.result.columns)} columns")
        self.next(self.join_features)

    # ── Step 5: join (fan-in) ──────────────────────────────────────────────────

    @step
    def join_features(self, inputs):
        """
        Fan-in: merges outputs from the three parallel feature steps.

        `inputs` is a list of the three branch states.
        Metaflow requires you to explicitly merge self attributes from branches.
        """
        agg, temporal, category = inputs[0].result, inputs[1].result, inputs[2].result

        merged = (
            agg
            .merge(temporal, on="customer_id", how="inner")
            .merge(category, on="customer_id", how="left")
        )
        cat_cols = [c for c in merged.columns if c.startswith("cat_")]
        merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)

        numeric_cols = [
            c for c in merged.select_dtypes(include=[np.number]).columns
            if c != "customer_id"
        ]
        merged[numeric_cols] = StandardScaler().fit_transform(merged[numeric_cols])

        self.features = merged
        print(f"[join] {merged.shape[0]} customers × {merged.shape[1]} features")
        self.next(self.end)

    # ── Step 6: save ───────────────────────────────────────────────────────────

    @step
    def end(self):
        """Persist feature store as Parquet."""
        import os
        import tempfile

        out_dir = tempfile.mkdtemp(prefix="metaflow_feature_store_")
        out_path = Path(out_dir) / "customer_features.parquet"
        self.features.to_parquet(out_path, index=False, engine="pyarrow")

        self.output_path = str(out_path)
        print(f"[end] Saved → {out_path}  ({os.path.getsize(out_path):,} bytes)")
        print(f"      {len(self.features)} customers × {len(self.features.columns)} features")
        print(f"      columns: {', '.join(self.features.columns)}")


if __name__ == "__main__":
    FeaturePipeline()
