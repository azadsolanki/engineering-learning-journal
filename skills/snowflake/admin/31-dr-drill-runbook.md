# Disaster Recovery Drill Runbook

> Step-by-step runbook for a planned failover drill using failover groups and client redirect. Builds on [09 Replication & Failover](09-replication-and-failover.md).

---

## Scenario

| | |
|:---|:---|
| Primary | `myorg.prod_us_west` |
| Secondary (DR) | `myorg.dr_us_east` |
| Failover group | `prod_fg` (databases, roles, users, warehouses, integrations) |
| Connection | `prod_conn` → `myorg-prod_conn.snowflakecomputing.com` |
| Targets | RPO ≤ 10 min, RTO ≤ 30 min |

---

## T-7 Days: Prep

- [ ] Announce the drill window to data consumers
- [ ] Confirm all apps and BI tools use the **connection URL**, not account URLs
- [ ] Confirm the latest refresh succeeded:

```sql
-- On secondary
SELECT phase_name, start_time, end_time
FROM TABLE(information_schema.replication_group_refresh_history('prod_fg'))
ORDER BY start_time DESC LIMIT 5;
```

- [ ] List things that **don't replicate** and need a plan (e.g., some integrations, external stage notifications, Snowpipe auto-ingest queues, tasks' running state)
- [ ] Prepare a validation query set: row counts and max timestamps on key tables

---

## T-0: Failover

| Step | Where | Action |
|:---|:---|:---|
| 1 | Primary | Pause writers: suspend task roots, pause pipes |
| 2 | Secondary | `ALTER FAILOVER GROUP prod_fg REFRESH;` (final sync) and wait for completion |
| 3 | Secondary | `ALTER FAILOVER GROUP prod_fg PRIMARY;` |
| 4 | Secondary | `ALTER CONNECTION prod_conn PRIMARY;` |
| 5 | New primary | Resume tasks and pipes |
| 6 | New primary | Run the validation queries |

```sql
-- Step 1 (old primary)
ALTER TASK transform.root_task SUSPEND;
ALTER PIPE raw.events_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Steps 2–4 (secondary)
ALTER FAILOVER GROUP prod_fg REFRESH;
ALTER FAILOVER GROUP prod_fg PRIMARY;
ALTER CONNECTION prod_conn PRIMARY;

-- Step 5 (new primary)
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('transform.root_task');
ALTER PIPE raw.events_pipe SET PIPE_EXECUTION_PAUSED = FALSE;
```

**Record the timestamps for each step.** They are your measured RTO.

---

## Validation

```sql
SELECT 'orders' AS tbl, COUNT(*) AS rows, MAX(updated_at) AS latest FROM analytics.orders
UNION ALL
SELECT 'customers', COUNT(*), MAX(updated_at) FROM analytics.crm.customers;
```

- [ ] Row counts match the pre-drill snapshot (allowing for the RPO window)
- [ ] BI dashboards load through the connection URL
- [ ] dbt / Airflow jobs run successfully
- [ ] SSO login works on the new primary
- [ ] Network policies and private endpoints are reachable

---

## Failback

Same steps in reverse once the drill is done:

```sql
-- On the original primary (now secondary)
ALTER FAILOVER GROUP prod_fg REFRESH;
ALTER FAILOVER GROUP prod_fg PRIMARY;
ALTER CONNECTION prod_conn PRIMARY;
```

---

## Drill Report Template

| Item | Result |
|:---|:---|
| Date / window | |
| Measured RTO (step 1 → step 6) | |
| Measured RPO (last refresh vs. failover time) | |
| What broke | |
| What didn't replicate that we expected to | |
| Action items + owners | |

> **💡 Tip:** The first drill always finds something: an app with a hard-coded account URL, a missing integration, a task that didn't resume. That's the point. Run drills at least twice a year.

## Checklist

- [ ] Runbook reviewed and stored where on-call can find it
- [ ] Drill completed and report filed
- [ ] Action items tracked to done
- [ ] Next drill scheduled
