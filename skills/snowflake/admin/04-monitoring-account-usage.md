# Snowflake Monitoring with ACCOUNT_USAGE

> Admin queries for spend, slow queries, storage and access auditing.

---

## ACCOUNT_USAGE vs INFORMATION_SCHEMA

| | `SNOWFLAKE.ACCOUNT_USAGE` | `<db>.INFORMATION_SCHEMA` |
|:---|:---|:---|
| Scope | Whole account | One database |
| Latency | ~45 min – 3 hrs | Real-time |
| Retention | 1 year | 7 days – 6 months (varies) |
| Dropped objects | Included | Not included |

Access needs `IMPORTED PRIVILEGES` on the SNOWFLAKE database (or the SNOWFLAKE database roles):

```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE snowflake TO ROLE platform_admin;
```

---

## 1. Credits by Warehouse (last 30 days)

```sql
SELECT warehouse_name,
       SUM(credits_used) AS credits
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits DESC;
```

## 2. Daily Credit Trend (all services)

```sql
SELECT usage_date,
       service_type,
       SUM(credits_used) AS credits
FROM snowflake.account_usage.metering_daily_history
WHERE usage_date > DATEADD(day, -30, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

## 3. Most Expensive Queries

```sql
SELECT query_id,
       user_name,
       warehouse_name,
       ROUND(credits_attributed_compute, 2) AS credits
FROM snowflake.account_usage.query_attribution_history
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY credits DESC
LIMIT 20;
```

## 4. Slow Queries & Spilling

Spilling to remote storage = warehouse too small for the query.

```sql
SELECT query_id,
       warehouse_name,
       warehouse_size,
       total_elapsed_time / 1000              AS seconds,
       bytes_spilled_to_local_storage  / 1e9  AS local_spill_gb,
       bytes_spilled_to_remote_storage / 1e9  AS remote_spill_gb,
       partitions_scanned, partitions_total
FROM snowflake.account_usage.query_history
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
  AND execution_status = 'SUCCESS'
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

> **💡 Tip:** `partitions_scanned` close to `partitions_total` on big tables means pruning isn't working — check filters or consider a clustering key.

## 5. Storage by Database

```sql
SELECT usage_date,
       database_name,
       average_database_bytes / POWER(1024, 4) AS db_tb,
       average_failsafe_bytes / POWER(1024, 4) AS failsafe_tb
FROM snowflake.account_usage.database_storage_usage_history
WHERE usage_date = DATEADD(day, -1, CURRENT_DATE())
ORDER BY db_tb DESC;
```

## 6. Who Has ACCOUNTADMIN?

```sql
SELECT grantee_name AS user_name, granted_by, created_on
FROM snowflake.account_usage.grants_to_users
WHERE role = 'ACCOUNTADMIN'
  AND deleted_on IS NULL;
```

## 7. Who Read a Sensitive Table? (Enterprise+)

```sql
SELECT ah.query_start_time,
       ah.user_name,
       obj.value:"objectName"::STRING AS object_name
FROM snowflake.account_usage.access_history ah,
     LATERAL FLATTEN(ah.base_objects_accessed) obj
WHERE obj.value:"objectName"::STRING = 'ANALYTICS.FINANCE.PAYROLL'
  AND ah.query_start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
ORDER BY 1 DESC;
```

## 8. Idle / Unused Warehouses

```sql
SHOW WAREHOUSES;
SELECT "name", "size", "auto_suspend", "resumed_on"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "resumed_on" < DATEADD(day, -30, CURRENT_TIMESTAMP());
```

---

## Automate It

Turn queries into alerts so problems surface without checking dashboards:

```sql
CREATE ALERT high_daily_spend
  WAREHOUSE = admin_wh
  SCHEDULE  = 'USING CRON 0 8 * * * America/Los_Angeles'
  IF (EXISTS (
    SELECT 1
    FROM snowflake.account_usage.metering_daily_history
    WHERE usage_date = DATEADD(day, -1, CURRENT_DATE())
    HAVING SUM(credits_used) > 100
  ))
  THEN CALL SYSTEM$SEND_EMAIL(
    'admin_email_int', 'me@company.com',
    'Snowflake spend alert', 'Yesterday used more than 100 credits.');

ALTER ALERT high_daily_spend RESUME;   -- alerts are created suspended
```
