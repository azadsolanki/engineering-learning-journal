"""Tasks 4 & 5: Merge feature sets and save to Parquet feature store."""
import pandas as pd
import numpy as np
from pathlib import Path
from flytekit import task, FlyteDirectory
from sklearn.preprocessing import StandardScaler


@task(cache=False)
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

    # Fill missing one-hot cols (customers with no category match)
    cat_cols = [c for c in merged.columns if c.startswith("cat_")]
    merged[cat_cols] = merged[cat_cols].fillna(0).astype(int)

    # Normalise continuous features for downstream ML compatibility
    numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "customer_id"]

    scaler = StandardScaler()
    merged[numeric_cols] = scaler.fit_transform(merged[numeric_cols])

    print(f"[merge] Final feature table: {merged.shape[0]} customers × {merged.shape[1]} features")
    return merged


@task(cache=False)
def save_feature_store(features: pd.DataFrame) -> FlyteDirectory:
    """
    Persists the merged feature table as Parquet.

    Returns a FlyteDirectory so downstream tasks or the workflow caller
    can retrieve the artifact path — exactly how a real feature store
    registration step would consume it.
    """
    import tempfile, os

    out_dir = tempfile.mkdtemp(prefix="feature_store_")
    out_path = Path(out_dir) / "customer_features.parquet"
    features.to_parquet(out_path, index=False, engine="pyarrow")

    meta_path = Path(out_dir) / "meta.txt"
    meta_path.write_text(
        f"rows={len(features)}\ncols={len(features.columns)}\n"
        f"columns={','.join(features.columns.tolist())}\n"
    )

    print(f"[output] Feature store saved → {out_path}  ({os.path.getsize(out_path):,} bytes)")
    return FlyteDirectory(path=out_dir)
