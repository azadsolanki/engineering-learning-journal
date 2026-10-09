# Hybrid Tables: Limitations & Availability

> What hybrid tables can't do (yet). Check this before promising them to an app team.

Verified against the [limitations page](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations) in Oct 2026. These change often, so re-check before a design decision.

---

## Availability

| | Supported? |
|:---|:---|
| AWS commercial regions | ✅ |
| Azure commercial regions | ✅ |
| Google Cloud | ❌ |
| U.S. SnowGov regions | ❌ |
| **Trial accounts** | ❌ |
| VPS | Contact Snowflake Support |

> **⚠️ Gotcha:** You can't try hybrid tables on a free trial account. Labs need a paid account in a supported region.

---

## Unsupported Features

| Feature | Impact for admins |
|:---|:---|
| **Replication** | Not in failover groups, so plan DR separately ([09](../admin/09-replication-and-failover.md)) |
| **Data sharing** | Can't share hybrid tables with consumers |
| **Fail-safe** | No 7-day disaster safety net |
| **UNDROP TABLE** | A dropped hybrid table is gone. `UNDROP SCHEMA/DATABASE` run but don't bring hybrid tables back |
| **Streams** | No CDC from hybrid tables with streams |
| **Dynamic tables** | Can't be built on hybrid tables |
| **Snowpipe / Snowpipe Streaming** | No continuous file ingestion |
| **Materialized views** | Not supported |
| **Clustering keys** | Data is ordered by primary key instead |
| **Search optimization / QAS** | Not supported (use secondary indexes) |
| **Result cache** | Queries don't use it |

### Time Travel (partial)

- Only `AT(TIMESTAMP => ...)` works, and the timestamp must be the same for all tables in the same database.
- No `OFFSET`, `STATEMENT`, `STREAM`, or `BEFORE`.

> **⚠️ Admin takeaway:** With no UNDROP, no Fail-safe and only partial Time Travel, **restrict `DROP` on hybrid tables**. Own them with a dedicated role, and keep your own backups, e.g. a scheduled CTAS into a standard table.

```sql
-- Simple nightly backup into a standard table
CREATE OR REPLACE TABLE backup.core.orders_snapshot AS
SELECT * FROM app.core.orders;
```

---

## Quotas & Throughput

| Limit | Value |
|:---|:---|
| Hybrid storage per database | **2 TB** of active row-store data. Writes that add data are blocked beyond this |
| Databases with hybrid tables | 200 per account, max 100 added per hour |
| Throughput (guide) | ~16,000 ops/sec per database for an 80/20 read/write mix |
| Request throttling | Per database |

- Space from **dropped/truncated** tables is reclaimed within seconds.
- Space from **deleted rows** takes hours (background compaction).

> **💡 Tip:** Throughput and storage are per database. Spreading high-traffic hybrid tables across databases raises the ceiling, but transactions and FKs can't cross databases, so split along app boundaries.

---

## Consistency

- A session always sees its own writes.
- Changes from **other** sessions can be stale by up to ~100 ms.
- Setting `READ_LATEST_WRITES = TRUE` avoids that staleness at a small latency cost.

---

## Other Limits

- `COPY INTO`: only `ON_ERROR = ABORT_STATEMENT`.
- `CHECK` constraints only at creation; `COPY INTO` fails if a CHECK constraint exists.
- `FILTER`, `REDUCE`, `TRANSFORM` higher-order functions aren't supported.
- Native Apps can use hybrid tables in the **consumer** account, but providers can't share them.

## Checklist

- [ ] Account is paid, in a supported AWS/Azure region
- [ ] DR plan doesn't rely on replication for hybrid tables
- [ ] DROP restricted; own backups scheduled
- [ ] Expected data size well under 2 TB per database
- [ ] No dependency on streams, dynamic tables or Snowpipe on these tables
