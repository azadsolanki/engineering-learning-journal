"""
Luigi Feature Engineering Pipeline
====================================
Luigi's caching model is file-system based and the simplest of all tools:
  - Every Task defines output() → a LocalTarget (file path)
  - If that file already EXISTS, Luigi considers the task DONE and skips it
  - No hash, no TTL, no server — just: does the output file exist?

This makes Luigi naturally idempotent. Delete an output file to rerun that step.

Task dependency graph mirrors the other POCs:
    IngestData
        ├── AggregationFeatures
        ├── TemporalFeatures
        └── CategoryFeatures
                    ↓
              MergeFeatures
                    ↓
             FeatureStore  (final Parquet output)
"""
import luigi
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler

OUTPUT_DIR = Path("output")


class IngestData(luigi.Task):
    csv_path = luigi.Parameter(default="data/orders.csv")

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "01_raw.parquet")

    def run(self):
        OUTPUT_DIR.mkdir(exist_ok=True)
        df = pd.read_csv(self.csv_path, parse_dates=["order_date"])
        df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
        df["order_amount"] = df["order_amount"].clip(lower=0)
        print(f"[ingest] {len(df)} rows, {df['customer_id'].nunique()} customers")
        df.to_parquet(self.output().path, index=False)


class AggregationFeatures(luigi.Task):
    csv_path = luigi.Parameter(default="data/orders.csv")

    def requires(self):
        return IngestData(csv_path=self.csv_path)

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "02_agg_features.parquet")

    def run(self):
        df = pd.read_parquet(self.input().path)
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
        print(f"[agg] {len(agg)} rows, {len(agg.columns)} columns")
        agg.to_parquet(self.output().path, index=False)


class TemporalFeatures(luigi.Task):
    csv_path = luigi.Parameter(default="data/orders.csv")

    def requires(self):
        return IngestData(csv_path=self.csv_path)

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "02_temporal_features.parquet")

    def run(self):
        df = pd.read_parquet(self.input().path).sort_values("order_date")
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
        temporal.to_parquet(self.output().path, index=False)


class CategoryFeatures(luigi.Task):
    csv_path = luigi.Parameter(default="data/orders.csv")

    def requires(self):
        return IngestData(csv_path=self.csv_path)

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "02_category_features.parquet")

    def run(self):
        df = pd.read_parquet(self.input().path)
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
        result = pd.concat([top_cat[["customer_id"]], dummies], axis=1)
        print(f"[category] {len(result)} rows, {len(result.columns)} columns")
        result.to_parquet(self.output().path, index=False)


class MergeFeatures(luigi.Task):
    csv_path = luigi.Parameter(default="data/orders.csv")

    def requires(self):
        return {
            "agg": AggregationFeatures(csv_path=self.csv_path),
            "temporal": TemporalFeatures(csv_path=self.csv_path),
            "category": CategoryFeatures(csv_path=self.csv_path),
        }

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "03_merged_features.parquet")

    def run(self):
        agg = pd.read_parquet(self.input()["agg"].path)
        temporal = pd.read_parquet(self.input()["temporal"].path)
        category = pd.read_parquet(self.input()["category"].path)

        merged = (
            agg
            .merge(temporal, on="customer_id", how="inner")
            .merge(category, on="customer_id", how="left")
        )
        cat_cols = [c for c in merged.columns if c.startswith("cat_")]
        merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)
        print(f"[merge] {merged.shape[0]} customers × {merged.shape[1]} features")
        merged.to_parquet(self.output().path, index=False)


class FeatureStore(luigi.Task):
    """
    Terminal task — produces the normalised feature store Parquet.

    This is the task you'd register in a feature store (Feast, Hopsworks, etc).
    Luigi's caching: if output/04_feature_store.parquet exists, this entire
    pipeline is considered complete and nothing re-runs.
    """
    csv_path = luigi.Parameter(default="data/orders.csv")

    def requires(self):
        return MergeFeatures(csv_path=self.csv_path)

    def output(self):
        return luigi.LocalTarget(OUTPUT_DIR / "04_feature_store.parquet")

    def run(self):
        merged = pd.read_parquet(self.input().path)
        numeric_cols = [
            c for c in merged.select_dtypes(include=[np.number]).columns
            if c != "customer_id"
        ]
        merged[numeric_cols] = StandardScaler().fit_transform(merged[numeric_cols])

        merged.to_parquet(self.output().path, index=False)
        import os
        print(f"[output] Feature store → {self.output().path}  "
              f"({os.path.getsize(self.output().path):,} bytes)")
        print(f"         {len(merged)} customers × {len(merged.columns)} features")
        print(f"         columns: {', '.join(merged.columns)}")
