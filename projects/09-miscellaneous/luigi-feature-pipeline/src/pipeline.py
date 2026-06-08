"""
Luigi pipeline entrypoint.

Usage:
    python src/pipeline.py                        # run full pipeline
    python src/pipeline.py --csv data/orders.csv  # explicit CSV path

Run twice — Luigi skips tasks whose output files already exist.
To rerun a step: delete the corresponding file in output/.
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import luigi
from src.tasks.pipeline import FeatureStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/orders.csv")
    args = parser.parse_args()

    luigi.build(
        [FeatureStore(csv_path=args.csv)],
        local_scheduler=True,
        log_level="INFO",
    )


if __name__ == "__main__":
    main()
