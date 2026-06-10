"""
Hamilton local runner — builds the Driver and executes the DAG.

Usage:
    python src/run.py
    python src/run.py --csv data/orders.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hamilton import driver
from src import features   # the module whose functions define the DAG


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/orders.csv")
    args = parser.parse_args()

    print("=" * 60)
    print("  Hamilton Feature Pipeline")
    print("=" * 60)

    # Driver builds the DAG by inspecting all functions in the `features` module
    dr = driver.Builder().with_modules(features).build()

    # Ask for the terminal output — Hamilton resolves and runs everything needed
    result = dr.execute(
        final_vars=["customer_feature_store"],
        inputs={"csv_path": args.csv},
    )

    store = result["customer_feature_store"]
    print()
    print(f"  customers : {len(store)}")
    print(f"  features  : {len(store.columns)}")
    print(f"  columns   : {', '.join(store.columns)}")

    import tempfile, os
    out_dir = tempfile.mkdtemp(prefix="hamilton_feature_store_")
    out = Path(out_dir) / "customer_features.parquet"
    store.to_parquet(out, index=False)
    print(f"\n  Output → {out}  ({os.path.getsize(out):,} bytes)")


if __name__ == "__main__":
    main()
