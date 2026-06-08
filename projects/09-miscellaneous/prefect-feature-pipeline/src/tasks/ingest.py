"""Task 1: Load and validate raw orders CSV."""
import pandas as pd
from prefect import task


REQUIRED_COLUMNS = {
    "order_id", "customer_id", "category",
    "order_amount", "order_date", "returned", "discount_pct",
}


@task(name="ingest-raw-data", log_prints=True)
def ingest_raw_data(csv_path: str) -> pd.DataFrame:
    """Loads raw CSV and performs schema validation."""
    df = pd.read_csv(csv_path, parse_dates=["order_date"])

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=["customer_id", "order_amount", "order_date"])
    df["order_amount"] = df["order_amount"].clip(lower=0)

    print(f"[ingest] Loaded {len(df)} rows, {df['customer_id'].nunique()} unique customers")
    return df
