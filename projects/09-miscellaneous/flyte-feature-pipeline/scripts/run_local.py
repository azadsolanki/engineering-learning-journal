"""
Local runner — executes the workflow in-process (no Flyte cluster required).

Usage:
    python scripts/run_local.py
    python scripts/run_local.py --csv data/orders.csv
"""
import argparse
import sys
from pathlib import Path

# Make src importable when running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from flytekit import FlyteFile
from src.workflow import feature_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the Flyte feature pipeline locally")
    parser.add_argument("--csv", default="data/orders.csv", help="Path to input CSV")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}")
        print("Run:  python scripts/generate_data.py  to create sample data first.")
        sys.exit(1)

    print("=" * 60)
    print("  Flyte Feature Engineering Pipeline  (local execution)")
    print("=" * 60)
    print(f"Input : {csv_path.resolve()}")
    print()

    result: FlyteFile = feature_pipeline(csv_path=FlyteFile(path=str(csv_path.resolve())))

    print()
    print("=" * 60)
    print(f"  Done!  Feature store → {result.path}")
    print("=" * 60)

    # Show what was written
    out = Path(result.path)
    for f in sorted(out.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:<35} {size:>10,} bytes")

    meta = out / "meta.txt"
    if meta.exists():
        print()
        print(meta.read_text())


if __name__ == "__main__":
    main()
