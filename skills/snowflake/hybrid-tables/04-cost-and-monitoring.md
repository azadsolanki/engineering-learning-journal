# Hybrid Tables: Cost & Monitoring

> What you pay for, where to see it, and how to tell whether the app's queries are actually fast.

---

## Cost Components

| Component | How it's billed |
|:---|:---|
| **Hybrid table storage** | Flat monthly rate per GB for the **row store**. Higher than standard storage (see the Service Consumption Table) |
| Columnar copy | **Not billed** |
| Time Travel data | Kept in object storage, billed at the **standard** storage rate |
| **Warehouse compute** | Normal warehouse credits, same as any query |

> **💡 Note:** The row store usually compresses worse than columnar storage, so the same data takes more GB as a hybrid table than as a standard table.

---

## Storage Monitoring

```sql
-- Account level: standard vs hybrid storage
SELECT usage_date,
       storage_bytes              / POWER(1024, 3) AS standard_gb,
       hybrid_table_storage_bytes / POWER(1024, 3) AS hybrid_gb
FROM snowflake.account_usage.storage_usage
ORDER BY usage_date DESC
LIMIT 30;

-- Per database (watch the 2 TB per-database quota)
SELECT usage_date, database_name,
       average_hybrid_table_storage_bytes / POWER(1024, 3) AS hybrid_gb,
       average_database_bytes             / POWER(1024, 3) AS standard_gb
FROM snowflake.account_usage.database_storage_usage_history
WHERE usage_date = DATEADD(day, -1, CURRENT_DATE())
  AND average_hybrid_table_storage_bytes > 0
ORDER BY hybrid_gb DESC;

-- Per table
SELECT *
FROM snowflake.account_usage.hybrid_tables
WHERE deleted IS NULL
ORDER BY bytes DESC;
```

> **💡 Tip:** Alert when a database passes ~70% of 2 TB (≈1.4 TB). Writes that add data are **blocked** at the quota (see [26 Alerts](../admin/26-alerts-and-notifications.md)).

---

## Query Performance: AGGREGATE_QUERY_HISTORY

Hybrid workloads run thousands of tiny queries per second. Instead of one `QUERY_HISTORY` row per query, short-running queries are **aggregated** by parameterized query shape over time intervals.

```sql
SELECT interval_start_time,
       query_parameterized_hash,
       ANY_VALUE(query_type)              AS query_type,
       SUM(calls)                         AS calls,
       AVG(total_elapsed_time:"avg"::NUMBER) AS avg_ms,
       MAX(total_elapsed_time:"p99"::NUMBER) AS p99_ms
FROM snowflake.account_usage.aggregate_query_history
WHERE interval_start_time > DATEADD(hour, -24, CURRENT_TIMESTAMP())
  AND warehouse_name = 'APP_WH'
GROUP BY 1, 2
ORDER BY calls DESC
LIMIT 50;
```

What to look for:

| Pattern | Likely cause | Fix |
|:---|:---|:---|
| Lookup shape with high p99 | Filter column not indexed | Add a secondary index ([02](02-creating-hybrid-tables.md)) |
| Writes getting slower over time | Too many indexes | Drop unused indexes |
| Errors spiking | Constraint violations, lock conflicts, throttling | Check app retries and per-database throughput |

---

## Warehouse Sizing for Hybrid Workloads

- Many tiny concurrent queries call for **multi-cluster** (scale out), not a bigger size (scale up).
- Keep the app on its **own warehouse**, separate from BI and ELT, so analytical scans don't add latency.
- A longer `AUTO_SUSPEND` avoids cold starts for a latency-sensitive app.

```sql
CREATE WAREHOUSE app_wh WITH
  WAREHOUSE_SIZE = 'XSMALL'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 4
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 600;
```

## Checklist

- [ ] Hybrid storage per database tracked against the 2 TB quota
- [ ] App queries reviewed in `AGGREGATE_QUERY_HISTORY` (p99, not just average)
- [ ] Dedicated multi-cluster warehouse for the app
- [ ] Unused indexes removed

**Docs:** [Evaluate cost for hybrid tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-cost)
