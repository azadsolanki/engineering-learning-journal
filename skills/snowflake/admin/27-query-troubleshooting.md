# Troubleshooting Slow & Stuck Queries

> A practical playbook: finding the problem query, reading the profile, and fixing the usual suspects.

---

## Step 1: Find the Query

```sql
-- Running right now (real-time, last 7 days available)
SELECT query_id, user_name, warehouse_name, execution_status,
       DATEDIFF(second, start_time, CURRENT_TIMESTAMP()) AS running_secs,
       LEFT(query_text, 100) AS query
FROM TABLE(information_schema.query_history(result_limit => 1000))
WHERE execution_status IN ('RUNNING', 'QUEUED', 'BLOCKED')
ORDER BY running_secs DESC;
```

## Step 2: Where Did the Time Go?

```sql
SELECT query_id,
       compilation_time / 1000         AS compile_s,
       queued_overload_time / 1000     AS queued_s,
       queued_provisioning_time / 1000 AS provisioning_s,
       transaction_blocked_time / 1000 AS blocked_s,
       execution_time / 1000           AS exec_s
FROM snowflake.account_usage.query_history
WHERE query_id = '<query_id>';
```

| Most time in... | Likely cause | Fix |
|:---|:---|:---|
| `queued_overload` | Warehouse busy | Multi-cluster / separate warehouse ([02](02-warehouses-and-cost-control.md)) |
| `queued_provisioning` | Warehouse resuming / resizing | Usually short. Ignore unless frequent |
| `transaction_blocked` | Waiting on a lock | See locks below |
| `compilation` | Huge SQL, many views, lots of metadata | Simplify, reduce nested views |
| `execution` | The query itself | Read the profile ↓ |

---

## Step 3: Read the Profile

Snowsight → Query History → query → **Query Profile**. Or in SQL:

```sql
SELECT operator_id, operator_type, operator_statistics, execution_time_breakdown
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query_id>'))
ORDER BY operator_id;
```

### The usual suspects

| Symptom in profile | Problem | Fix |
|:---|:---|:---|
| Join output rows ≫ input rows | **Exploding join** (missing or duplicate keys) | Check join keys, dedupe first |
| "Bytes spilled to remote storage" | Not enough memory | Bigger warehouse, or reduce data before the join/sort |
| Partitions scanned ≈ partitions total | **No pruning** | Filter on clustered columns, avoid functions on filter columns ([13](13-clustering-and-performance.md)) |
| `UNION` instead of `UNION ALL` | Unneeded dedup sort | Use `UNION ALL` when duplicates are fine |
| Huge `ORDER BY` with no `LIMIT` | Global sort of everything | Remove it or add a `LIMIT` |
| Remote disk I/O dominates | Cold cache | Normal after resume; consider a longer `AUTO_SUSPEND` for BI |

> **💡 Tip:** `WHERE TO_DATE(event_ts) = '2026-10-01'` can block pruning. Prefer `WHERE event_ts >= '2026-10-01' AND event_ts < '2026-10-02'`.

---

## Stuck: Locks & Transactions

```sql
SHOW LOCKS IN ACCOUNT;
SHOW TRANSACTIONS IN ACCOUNT;

-- Kill a blocking transaction
SELECT SYSTEM$ABORT_TRANSACTION(<transaction_id>);
```

Common cause: a session ran `BEGIN` and never committed, so its `UPDATE`/`MERGE` holds the lock. Fix the client (autocommit), and set `LOCK_TIMEOUT` if needed.

---

## Killing Queries

```sql
SELECT SYSTEM$CANCEL_QUERY('<query_id>');
ALTER USER jdoe ABORT ALL QUERIES;
ALTER WAREHOUSE adhoc_wh ABORT ALL QUERIES;
```

Prevent repeats with `STATEMENT_TIMEOUT_IN_SECONDS` on the warehouse ([21](21-parameters.md)).

---

## Recurring Offenders

```sql
-- Same query shape that's slow over and over
SELECT query_parameterized_hash,
       COUNT(*)                         AS runs,
       AVG(total_elapsed_time) / 1000   AS avg_s,
       ANY_VALUE(LEFT(query_text, 100)) AS sample
FROM snowflake.account_usage.query_history
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY 1
HAVING runs > 10
ORDER BY avg_s * runs DESC
LIMIT 20;
```

## Checklist

- [ ] Know the "find → time breakdown → profile" sequence
- [ ] Timeouts set so runaway queries end on their own
- [ ] Weekly review of top recurring slow query hashes
