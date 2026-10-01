# Snowflake Streams & Tasks

> Change data capture with streams, scheduling with tasks, and running task graphs in production.

---

## Streams (CDC)

A stream tracks changes to a table since the last time the stream was consumed.

```sql
CREATE STREAM raw.orders_stream ON TABLE raw.orders;
CREATE STREAM raw.events_stream ON TABLE raw.events APPEND_ONLY = TRUE;   -- inserts only, cheaper
```

Extra columns on every stream row:

| Column | Meaning |
|:---|:---|
| `METADATA$ACTION` | `INSERT` or `DELETE` |
| `METADATA$ISUPDATE` | `TRUE` if the row is half of an update (DELETE + INSERT pair) |
| `METADATA$ROW_ID` | Stable row ID |

> **💡 Key rule:** A stream's offset only moves when the stream is used in a **DML statement that commits**. A plain `SELECT` doesn't consume it.

> **⚠️ Gotcha (staleness):** If a stream isn't consumed within the table's retention period (extended up to `MAX_DATA_EXTENSION_TIME_IN_DAYS`, default 14), it goes **stale** and must be recreated. Check `SHOW STREAMS` → `stale_after`.

---

## Tasks

```sql
CREATE TASK transform.merge_orders
  WAREHOUSE = transform_wh                -- or omit for serverless
  SCHEDULE  = '5 MINUTE'                  -- or 'USING CRON 0 * * * * UTC'
  WHEN SYSTEM$STREAM_HAS_DATA('raw.orders_stream')   -- skip run (no cost) if empty
AS
  MERGE INTO analytics.orders t
  USING (SELECT * FROM raw.orders_stream WHERE METADATA$ACTION = 'INSERT') s
    ON t.order_id = s.order_id
  WHEN MATCHED THEN UPDATE SET t.status = s.status, t.updated_at = s.updated_at
  WHEN NOT MATCHED THEN INSERT (order_id, status, updated_at)
                        VALUES (s.order_id, s.status, s.updated_at);

ALTER TASK transform.merge_orders RESUME;   -- tasks are created SUSPENDED
```

### Serverless vs warehouse tasks

| | Serverless | Warehouse |
|:---|:---|:---|
| Setup | Omit `WAREHOUSE`; optionally `USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE` | Set `WAREHOUSE = ...` |
| Billing | Compute used by the task | Warehouse time (60s minimum per resume) |
| Good for | Short, frequent tasks | Long jobs, or sharing an already-running warehouse |

---

## Task Graphs (DAGs)

```sql
CREATE TASK transform.root_task
  SCHEDULE = 'USING CRON 0 2 * * * America/Los_Angeles'
AS SELECT 1;

CREATE TASK transform.load_dims   AFTER transform.root_task AS CALL load_dims();
CREATE TASK transform.load_facts  AFTER transform.load_dims AS CALL load_facts();
CREATE TASK transform.refresh_agg AFTER transform.load_facts AS CALL refresh_agg();

-- Resume the whole graph (children first, then root) in one call
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('transform.root_task');
```

> **⚠️ Gotcha:** To modify a task in a graph, suspend the **root** task first. Remember to resume it afterwards.

---

## Admin Setup

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE task_admin;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE task_admin;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE task_admin;   -- for serverless
GRANT ROLE task_admin TO ROLE data_engineer;
```

---

## Monitoring

```sql
SHOW TASKS IN DATABASE analytics;

-- Failures in the last day
SELECT name, state, error_message, scheduled_time, completed_time
FROM TABLE(information_schema.task_history(
  scheduled_time_range_start => DATEADD(day, -1, CURRENT_TIMESTAMP())))
WHERE state = 'FAILED'
ORDER BY scheduled_time DESC;

-- Manually trigger a run
EXECUTE TASK transform.merge_orders;
```

> **💡 Tip:** Set `ERROR_INTEGRATION` on a root task to push failure notifications to SNS / Event Grid / Pub/Sub. Or simplify the whole pipeline with **dynamic tables** when you just need "keep this table fresh within N minutes".

## Checklist

- [ ] `WHEN SYSTEM$STREAM_HAS_DATA` on stream-driven tasks
- [ ] Stream staleness monitored
- [ ] Task failures alerted on
- [ ] `EXECUTE TASK` granted to a dedicated role, not ACCOUNTADMIN
