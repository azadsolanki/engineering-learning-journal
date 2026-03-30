"""
Apache Iceberg Hands-On Lab
Covers: table creation, insert, schema evolution, time travel, partitioning
"""

import json
import os
import shutil

import pyarrow as pa
from pyiceberg.catalog.sql import SqlCatalog

# ─── 0. Setup ─────────────────────────────────────────────────────────────────
LAB_DIR = "/home/claude/iceberg_lab"
if os.path.exists(LAB_DIR):
    shutil.rmtree(LAB_DIR)
os.makedirs(LAB_DIR)

catalog = SqlCatalog(
    "local",
    **{
        "uri": f"sqlite:///{LAB_DIR}/catalog.db",
        "warehouse": f"file://{LAB_DIR}/warehouse",
    },
)
catalog.create_namespace("shop")
print("✅ Catalog created (SQLite-backed, local filesystem warehouse)\n")

# ─── 1. Create an Iceberg Table ───────────────────────────────────────────────
from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.transforms import MonthTransform
from pyiceberg.types import (
    FloatType,
    IntegerType,
    NestedField,
    StringType,
    TimestampType,
)

# required=False matches PyArrow's nullable default
orders_schema = Schema(
    NestedField(1, "order_id", StringType(), required=False),
    NestedField(2, "customer_id", StringType(), required=False),
    NestedField(3, "product", StringType(), required=False),
    NestedField(4, "quantity", IntegerType(), required=False),
    NestedField(5, "total_usd", FloatType(), required=False),
    NestedField(6, "order_ts", TimestampType(), required=False),
)

partition_spec = PartitionSpec(
    PartitionField(
        source_id=6, field_id=1000, transform=MonthTransform(), name="order_ts_month"
    )
)

table = catalog.create_table(
    "shop.orders",
    schema=orders_schema,
    partition_spec=partition_spec,
)
print("✅ Table shop.orders created")
print(f"   Fields:    {[f.name for f in table.schema().fields]}")
print(f"   Partition: month(order_ts)")
print(f"   Location:  {table.location()}\n")

# ─── 2. Insert Data → Snapshot 1 ─────────────────────────────────────────────
from datetime import datetime

batch1 = pa.table(
    {
        "order_id": ["O001", "O002", "O003", "O004", "O005"],
        "customer_id": ["C1", "C2", "C1", "C3", "C2"],
        "product": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones"],
        "quantity": pa.array([1, 2, 1, 1, 3], type=pa.int32()),
        "total_usd": pa.array(
            [999.99, 29.98, 79.99, 399.00, 149.97], type=pa.float32()
        ),
        "order_ts": pa.array(
            [
                datetime(2024, 1, 10),
                datetime(2024, 1, 15),
                datetime(2024, 2, 5),
                datetime(2024, 2, 20),
                datetime(2024, 3, 1),
            ],
            type=pa.timestamp("us"),
        ),
    }
)

table.append(batch1)
snap1 = table.current_snapshot()
print("✅ Snapshot 1  —  INSERT 5 rows")
print(f"   snapshot_id : {snap1.snapshot_id}")
print(f"   operation   : {snap1.summary.operation.value}\n")

# ─── 3. Second Append → Snapshot 2 ───────────────────────────────────────────
batch2 = pa.table(
    {
        "order_id": ["O006", "O007", "O008"],
        "customer_id": ["C4", "C1", "C5"],
        "product": ["Webcam", "USB Hub", "Desk Lamp"],
        "quantity": pa.array([1, 1, 2], type=pa.int32()),
        "total_usd": pa.array([89.99, 49.99, 65.0], type=pa.float32()),
        "order_ts": pa.array(
            [
                datetime(2024, 3, 10),
                datetime(2024, 3, 22),
                datetime(2024, 4, 2),
            ],
            type=pa.timestamp("us"),
        ),
    }
)

table.append(batch2)
snap2 = table.current_snapshot()
print("✅ Snapshot 2  —  INSERT 3 more rows")
print(f"   snapshot_id : {snap2.snapshot_id}\n")

# ─── 4. Read current state ────────────────────────────────────────────────────
df_current = table.scan().to_arrow()
print(f"✅ Current scan  →  {len(df_current)} rows")
print(f"   Products: {df_current['product'].to_pylist()}\n")

# ─── 5. Time Travel  →  back to Snapshot 1 ───────────────────────────────────
df_past = table.scan(snapshot_id=snap1.snapshot_id).to_arrow()
print(f"✅ Time travel to snapshot 1  →  {len(df_past)} rows")
print(f"   Products: {df_past['product'].to_pylist()}\n")

# ─── 6. Schema Evolution — add a column ──────────────────────────────────────
with table.update_schema() as upd:
    upd.add_column("discount_pct", FloatType(), "Discount % applied (optional)")

print("✅ Schema evolved  —  added column 'discount_pct'")
print(f"   New fields: {[f.name for f in table.schema().fields]}")

# Old rows return None for the new column — fully backwards compatible
df_evolved = table.scan().to_arrow()
sample_discounts = df_evolved["discount_pct"].to_pylist()[:3]
print(
    f"   Existing rows discount_pct = {sample_discounts}  (None = backwards compat)\n"
)

# ─── 7. Snapshot history ─────────────────────────────────────────────────────
print("✅ Snapshot history:")
for entry in table.history():
    print(f"   id={entry.snapshot_id}  ts={entry.timestamp_ms}")
print()

# ─── 8. Inspect partitions actually written ───────────────────────────────────
print("✅ Data files by partition:")
for task in table.scan().plan_files():
    fname = task.file.file_path.split("/")[-1]
    rows = task.file.record_count
    size = task.file.file_size_in_bytes
    print(f"   {fname}  rows={rows}  bytes={size}")
print()

# ─── 9. Peek inside the metadata JSON ────────────────────────────────────────
meta_path = table.metadata_location.replace("file://", "")
with open(meta_path) as f:
    meta = json.load(f)
print("✅ metadata.json summary:")
print(f"   format-version       : {meta['format-version']}")
print(f"   schemas stored       : {len(meta['schemas'])}")
print(f"   snapshots stored     : {len(meta['snapshots'])}")
print(f"   current-snapshot-id  : {meta['current-snapshot-id']}")
print()
print("🎉  Lab complete!")
