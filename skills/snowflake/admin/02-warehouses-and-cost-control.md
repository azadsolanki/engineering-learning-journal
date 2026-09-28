# Snowflake Warehouses & Cost Control

> Sizing, scaling and guarding virtual warehouses so compute spend stays predictable.

---

## How Billing Works

- Compute is billed in **credits** per second while a warehouse runs (60-second minimum each time it resumes).
- Each size up **doubles** credits/hour and (roughly) compute power.

| Size | Credits / hour |
|:---|:---|
| X-Small | 1 |
| Small | 2 |
| Medium | 4 |
| Large | 8 |
| X-Large | 16 |

> **💡 Rule of thumb:** Scale **up** (bigger size) for slow, complex queries. Scale **out** (multi-cluster) for many concurrent queries.

---

## Creating a Warehouse

```sql
USE ROLE SYSADMIN;
CREATE WAREHOUSE bi_wh WITH
  WAREHOUSE_SIZE      = 'SMALL'
  AUTO_SUSPEND        = 60        -- seconds idle before suspend
  AUTO_RESUME         = TRUE
  INITIALLY_SUSPENDED = TRUE
  MIN_CLUSTER_COUNT   = 1
  MAX_CLUSTER_COUNT   = 3         -- multi-cluster (Enterprise+)
  SCALING_POLICY      = 'STANDARD'
  STATEMENT_TIMEOUT_IN_SECONDS = 3600
  COMMENT = 'BI dashboards';
```

| Setting | Why it matters |
|:---|:---|
| `AUTO_SUSPEND` | Biggest cost lever. 60s is a good default; very low values lose the local cache |
| `SCALING_POLICY` | `STANDARD` adds clusters quickly; `ECONOMY` waits until a cluster would stay busy |
| `STATEMENT_TIMEOUT_IN_SECONDS` | Kills runaway queries (default is 2 days!) |

---

## Workload Isolation

Separate warehouses per workload so one team can't starve another and costs are attributable:

```
LOAD_WH       → ingestion (COPY, Snowpipe tasks)
TRANSFORM_WH  → dbt / ELT
BI_WH         → dashboards (multi-cluster)
ADHOC_WH      → analysts, data science
```

---

## Resource Monitors

Resource monitors track credit usage and can notify or suspend warehouses. Only **ACCOUNTADMIN** can create them.

```sql
USE ROLE ACCOUNTADMIN;
CREATE RESOURCE MONITOR bi_monthly WITH
  CREDIT_QUOTA    = 200
  FREQUENCY       = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75  PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND            -- lets running queries finish
    ON 110 PERCENT DO SUSPEND_IMMEDIATE; -- cancels running queries

ALTER WAREHOUSE bi_wh SET RESOURCE_MONITOR = bi_monthly;

-- Account-wide cap
ALTER ACCOUNT SET RESOURCE_MONITOR = account_cap;
```

> **⚠️ Gotcha:** Resource monitors only cover **warehouse** credits. Serverless features (Snowpipe, auto-clustering, serverless tasks, etc.) and cloud services are not stopped by them — use budgets / usage views for those.

---

## Useful Commands

```sql
SHOW WAREHOUSES;
ALTER WAREHOUSE adhoc_wh SET WAREHOUSE_SIZE = 'MEDIUM';
ALTER WAREHOUSE adhoc_wh SUSPEND;
SHOW RESOURCE MONITORS;

-- Queued queries = need scale-out; long execution = need scale-up
SELECT warehouse_name,
       AVG(avg_running)       AS running,
       AVG(avg_queued_load)   AS queued
FROM snowflake.account_usage.warehouse_load_history
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY queued DESC;
```

## Checklist

- [ ] Every warehouse has `AUTO_SUSPEND` and `AUTO_RESUME`
- [ ] `STATEMENT_TIMEOUT_IN_SECONDS` set on warehouses (or account)
- [ ] Every warehouse attached to a resource monitor
- [ ] One warehouse per workload type
