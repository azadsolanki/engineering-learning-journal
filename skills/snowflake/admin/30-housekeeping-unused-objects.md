# Housekeeping: Finding Unused Objects

> Regular cleanup of tables, users, roles and warehouses nobody uses. It cuts cost and attack surface.

---

## Why Bother

| Clutter | Cost | Risk |
|:---|:---|:---|
| Tables nobody reads | Storage + Time Travel + Fail-safe | Stale data used by mistake |
| Users who never log in | Nothing | Unused credentials = attack surface |
| Roles with no members | Nothing | Confusing grant model |
| Idle warehouses | None while suspended | Someone resumes the wrong one |
| Old dev clones | Storage drift | Copies of prod data with weaker controls |

---

## Tables Not Read in 90 Days (Enterprise+)

```sql
WITH last_read AS (
  SELECT obj.value:"objectName"::STRING AS table_name,
         MAX(ah.query_start_time)       AS last_read_at
  FROM snowflake.account_usage.access_history ah,
       LATERAL FLATTEN(ah.base_objects_accessed) obj
  WHERE obj.value:"objectDomain"::STRING = 'Table'
  GROUP BY 1
)
SELECT t.table_catalog || '.' || t.table_schema || '.' || t.table_name AS table_name,
       t.bytes / POWER(1024, 3) AS gb,
       lr.last_read_at
FROM snowflake.account_usage.tables t
LEFT JOIN last_read lr
  ON lr.table_name = t.table_catalog || '.' || t.table_schema || '.' || t.table_name
WHERE t.deleted IS NULL
  AND t.table_type = 'BASE TABLE'
  AND (lr.last_read_at IS NULL OR lr.last_read_at < DATEADD(day, -90, CURRENT_TIMESTAMP()))
ORDER BY gb DESC NULLS LAST
LIMIT 50;
```

> **⚠️ Gotcha:** `ACCESS_HISTORY` only goes back one year, and some tables are only read once a year (audits, year-end). Confirm with the owner before dropping. Rename first (`ALTER TABLE ... RENAME TO zz_deprecated_...`), drop later. Time Travel still allows `UNDROP`.

---

## Users

```sql
-- Never logged in, or not in 90 days
SELECT name, type, created_on, last_success_login, disabled
FROM snowflake.account_usage.users
WHERE deleted_on IS NULL
  AND disabled = FALSE
  AND (last_success_login IS NULL
       OR last_success_login < DATEADD(day, -90, CURRENT_TIMESTAMP()))
ORDER BY last_success_login NULLS FIRST;
```

Disable rather than drop at first: `ALTER USER x SET DISABLED = TRUE;`

---

## Roles

```sql
-- Custom roles granted to no user and no other role
SELECT r.name AS role_name, r.created_on
FROM snowflake.account_usage.roles r
WHERE r.deleted_on IS NULL
  AND r.name NOT IN ('ACCOUNTADMIN','SECURITYADMIN','USERADMIN','SYSADMIN','ORGADMIN','PUBLIC')
  AND NOT EXISTS (SELECT 1 FROM snowflake.account_usage.grants_to_users u
                  WHERE u.role = r.name AND u.deleted_on IS NULL)
  AND NOT EXISTS (SELECT 1 FROM snowflake.account_usage.grants_to_roles g
                  WHERE g.granted_on = 'ROLE' AND g.name = r.name
                    AND g.privilege = 'USAGE' AND g.deleted_on IS NULL);
```

---

## Warehouses

```sql
-- Warehouses with no credits used in 60 days
SELECT w.warehouse_name
FROM (SELECT DISTINCT warehouse_name
      FROM snowflake.account_usage.warehouse_metering_history) w
WHERE w.warehouse_name NOT IN (
  SELECT warehouse_name
  FROM snowflake.account_usage.warehouse_metering_history
  WHERE start_time > DATEADD(day, -60, CURRENT_TIMESTAMP())
);
```

---

## Clones, Stages & Leftovers

```sql
SHOW DATABASES LIKE '%_DEV%';
SHOW DATABASES LIKE '%_CLONE%';

-- Files sitting in internal stages (storage you pay for)
SELECT stage_name, SUM(average_stage_bytes) / POWER(1024, 3) AS gb
FROM snowflake.account_usage.stage_storage_usage_history
WHERE usage_date = DATEADD(day, -1, CURRENT_DATE())
GROUP BY 1;
```

---

## Make It a Routine

1. Run these queries **monthly** (a task can write results to an `admin.housekeeping` table).
2. Send the list to object owners (tags help, see [08](08-object-tagging-and-classification.md)).
3. **Rename/disable** → wait 30 days → **drop**.
4. Track storage and object counts over time to show the impact.

## Checklist

- [ ] Monthly unused-object report
- [ ] Rename-then-drop process agreed with teams
- [ ] Dormant users disabled automatically after N days
- [ ] Orphan roles and old clones cleaned up
