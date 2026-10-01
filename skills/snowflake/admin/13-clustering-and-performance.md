# Snowflake Clustering & Performance Features

> Clustering keys, search optimization, query acceleration and caching: when each one is worth paying for.

---

## Decision Guide

| Problem | Feature | Edition |
|:---|:---|:---|
| Big table, range filters (dates) scan too many partitions | **Clustering key** | All |
| Point lookups (`WHERE id = ...`) on huge tables | **Search optimization** | Enterprise+ |
| Occasional huge scans slow down a warehouse | **Query acceleration** | Enterprise+ |
| Same expensive aggregation queried over and over | **Materialized view** | Enterprise+ |
| Identical queries re-run | **Result cache** (free, 24h) | All |

---

## Micro-partitions & Pruning

Snowflake stores tables in micro-partitions (~16 MB compressed) and keeps min/max stats per column. Filters skip partitions whose ranges don't match. This is **pruning**.

```sql
-- How well is a table clustered on a column?
SELECT SYSTEM$CLUSTERING_INFORMATION('analytics.events', '(event_date)');
-- Look at average_depth: closer to 1 = better pruning
```

---

## Clustering Keys

Only worth it when the table is **multi-TB**, queries filter on the same columns, and the table isn't mostly rewritten constantly.

```sql
ALTER TABLE analytics.events CLUSTER BY (event_date, customer_id);

-- Automatic clustering runs serverless in the background; pause if needed
ALTER TABLE analytics.events SUSPEND RECLUSTER;
ALTER TABLE analytics.events RESUME RECLUSTER;

ALTER TABLE analytics.events DROP CLUSTERING KEY;
```

> **💡 Tip:** Put the lowest-cardinality column first. For timestamps, cluster on an expression like `TO_DATE(event_ts)` rather than the raw timestamp.

---

## Search Optimization

Builds a search access path for selective lookups (equality, `IN`, substring, geo, VARIANT fields).

```sql
-- Estimate cost first
SELECT SYSTEM$ESTIMATE_SEARCH_OPTIMIZATION_COSTS('analytics.events');

ALTER TABLE analytics.events
  ADD SEARCH OPTIMIZATION ON EQUALITY(customer_id), SUBSTRING(user_agent);

DESC SEARCH OPTIMIZATION ON analytics.events;
```

---

## Query Acceleration Service (QAS)

Offloads parts of large scans to serverless compute, so outlier queries don't need a bigger warehouse.

```sql
-- Would this query have benefited?
SELECT SYSTEM$ESTIMATE_QUERY_ACCELERATION('<query_id>');

ALTER WAREHOUSE adhoc_wh SET
  ENABLE_QUERY_ACCELERATION = TRUE
  QUERY_ACCELERATION_MAX_SCALE_FACTOR = 8;   -- cap at 8x warehouse size
```

---

## Caching Layers

| Cache | Where | Lasts | Note |
|:---|:---|:---|:---|
| Result cache | Cloud services | 24 h (up to 31 days if reused) | Free; needs an identical query and unchanged data |
| Warehouse (local disk) cache | Warehouse SSD | Until suspend | Lost on suspend, which is why very short `AUTO_SUSPEND` can hurt BI |
| Metadata cache | Cloud services | Always | `COUNT(*)`, `MIN/MAX` can return without a warehouse |

---

## Watch the Serverless Bill

All of these features cost credits in the background:

```sql
SELECT 'clustering' AS feature, table_name AS object, SUM(credits_used) AS credits
FROM snowflake.account_usage.automatic_clustering_history
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP()) GROUP BY 2
UNION ALL
SELECT 'search_opt', table_name, SUM(credits_used)
FROM snowflake.account_usage.search_optimization_history
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP()) GROUP BY 2
UNION ALL
SELECT 'qas', warehouse_name, SUM(credits_used)
FROM snowflake.account_usage.query_acceleration_history
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP()) GROUP BY 2
ORDER BY credits DESC;
```

## Checklist

- [ ] Clustering keys only on large tables with poor pruning (check `average_depth`)
- [ ] Search optimization cost estimated before enabling
- [ ] QAS scale factor capped
- [ ] Serverless feature credits reviewed monthly
