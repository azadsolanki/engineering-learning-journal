# Snowflake Parameters

> Where settings live, how they inherit, and the ones every admin should set on day one.

---

## Three Kinds of Parameters

| Type | Set on | Example |
|:---|:---|:---|
| **Account** | Account only | `PERIODIC_DATA_REKEYING`, `REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION` |
| **Session** | Account → user → session | `TIMEZONE`, `QUERY_TAG`, `STATEMENT_TIMEOUT_IN_SECONDS` |
| **Object** | Account → database → schema → table, or warehouse | `DATA_RETENTION_TIME_IN_DAYS`, `MAX_CLUSTER_COUNT` |

The **most specific** level wins:

```
Session params:  ACCOUNT  →  USER  →  SESSION          (session wins)
Object params:   ACCOUNT  →  DATABASE → SCHEMA → TABLE (table wins)
```

---

## Viewing Parameters

```sql
SHOW PARAMETERS IN ACCOUNT;
SHOW PARAMETERS IN SESSION;
SHOW PARAMETERS IN USER jdoe;
SHOW PARAMETERS IN WAREHOUSE bi_wh;
SHOW PARAMETERS LIKE 'STATEMENT_TIMEOUT%' IN ACCOUNT;
```

The `level` column shows where the current value was set (`ACCOUNT`, `USER`, `SESSION`, or blank for default).

## Setting & Resetting

```sql
ALTER ACCOUNT   SET TIMEZONE = 'UTC';
ALTER USER jdoe SET TIMEZONE = 'America/Los_Angeles';
ALTER SESSION   SET QUERY_TAG = 'dbt:nightly';

ALTER ACCOUNT UNSET TIMEZONE;   -- back to default
```

---

## Day-One Parameters

| Parameter | Level | Suggested | Why |
|:---|:---|:---|:---|
| `STATEMENT_TIMEOUT_IN_SECONDS` | Account / warehouse | `7200` | Default is 2 days; stops runaway queries |
| `STATEMENT_QUEUED_TIMEOUT_IN_SECONDS` | Account / warehouse | `1800` | Don't queue forever behind a busy warehouse |
| `TIMEZONE` | Account | `'UTC'` | Consistent timestamps across tools |
| `DATA_RETENTION_TIME_IN_DAYS` | Account / db | `1`–`30` | Time Travel window ([05](05-time-travel-and-failsafe.md)) |
| `MIN_DATA_RETENTION_TIME_IN_DAYS` | Account | `7` | Floor nobody can go below |
| `PERIODIC_DATA_REKEYING` | Account | `TRUE` | [19](19-encryption-and-private-connectivity.md) |
| `REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION` | Account | `TRUE` | No inline cloud keys ([18](18-external-access-and-secrets.md)) |
| `PREVENT_UNLOAD_TO_INLINE_URL` | Account | `TRUE` | Blocks `COPY INTO 's3://random-bucket'` data exfiltration |
| `ABORT_DETACHED_QUERY` | Account | `TRUE` | Cancel queries when the client disconnects |
| `NETWORK_POLICY` | Account / user | your policy | [03](03-users-auth-network-security.md) |

---

## QUERY_TAG for Cost Attribution

Tag queries from each tool, then group cost by tag:

```sql
-- In dbt, Airflow, BI service users:
ALTER USER svc_dbt SET QUERY_TAG = 'team:analytics;tool:dbt';

SELECT q.query_tag, SUM(a.credits_attributed_compute) AS credits
FROM snowflake.account_usage.query_attribution_history a
JOIN snowflake.account_usage.query_history q USING (query_id)
WHERE q.start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits DESC;
```

> **⚠️ Gotcha:** Users can override session parameters (like `QUERY_TAG`) themselves, so treat them as attribution hints, not security controls. Real controls are account parameters and policies.

## Checklist

- [ ] Statement and queue timeouts set
- [ ] Account timezone standardized
- [ ] Exfiltration guardrails on (`PREVENT_UNLOAD_TO_INLINE_URL`, storage integrations required)
- [ ] `QUERY_TAG` set on every service user
