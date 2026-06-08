"""Tasks 5-6: Merge feature sets and save to Parquet."""
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
from prefect import task
from sklearn.preprocessing import StandardScaler


@task(name="merge-features", log_prints=True)
def merge_features(
    agg_features: pd.DataFrame,
    temporal_features: pd.DataFrame,
    category_features: pd.DataFrame,
) -> pd.DataFrame:
    """Joins all feature tables on customer_id into a single wide table."""
    print("[merge] Merging feature tables ...")

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

    print(f"[merge] Final table: {merged.shape[0]} customers × {merged.shape[1]} features")
    return merged


@task(name="save-feature-store", log_prints=True)
def save_feature_store(features: pd.DataFrame) -> str:
    """Persists merged features as Parquet and returns the output directory path."""
    import os

    out_dir = tempfile.mkdtemp(prefix="prefect_feature_store_")
    out_path = Path(out_dir) / "customer_features.parquet"
    features.to_parquet(out_path, index=False, engine="pyarrow")

    meta_path = Path(out_dir) / "meta.txt"
    meta_path.write_text(
        f"rows={len(features)}\ncols={len(features.columns)}\n"
        f"columns={','.join(features.columns.tolist())}\n"
    )

    print(f"[output] Saved → {out_path}  ({os.path.getsize(out_path):,} bytes)")
    return out_dir
