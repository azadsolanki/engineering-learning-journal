# Snowflake Budgets & Cost Anomalies

> Tracking *all* spend, serverless included, against limits, and catching unusual spikes early.

---

## Resource Monitors vs Budgets

| | Resource monitor | Budget |
|:---|:---|:---|
| Covers | Warehouses only | Warehouses **and** serverless features (pipes, tasks, clustering, MVs, etc.) |
| Action | Notify, or **suspend** warehouses | Notify (email, cloud queue, webhook) or call a stored procedure |
| Period | Configurable | Monthly |
| Best for | Hard stop on warehouse credits | Overall spend tracking per team / project |

> **💡 Rule of thumb:** Use both. Resource monitors are the hard brakes on compute. Budgets are the dashboard for everything else.

---

## Account Budget

One per account. It tracks total credit usage.

```sql
USE ROLE ACCOUNTADMIN;
CALL snowflake.local.account_root_budget!ACTIVATE();
CALL snowflake.local.account_root_budget!SET_SPENDING_LIMIT(5000);   -- credits / month

CALL snowflake.local.account_root_budget!SET_EMAIL_NOTIFICATIONS(
  'admin_email_int', 'platform-team@company.com');
```

---

## Custom Budgets

Group specific objects (warehouses, databases, pipes, tasks...) into a budget per team or project.

```sql
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS admin;
CREATE SCHEMA IF NOT EXISTS admin.budgets;

-- Delegate budget creation
GRANT DATABASE ROLE snowflake.budget_creator TO ROLE platform_admin;
GRANT CREATE SNOWFLAKE.CORE.BUDGET ON SCHEMA admin.budgets TO ROLE platform_admin;

USE ROLE platform_admin;
CREATE SNOWFLAKE.CORE.BUDGET admin.budgets.marketing_budget();
CALL admin.budgets.marketing_budget!SET_SPENDING_LIMIT(400);

-- Add objects to it (the owner of each object must allow it via APPLYBUDGET)
CALL admin.budgets.marketing_budget!ADD_RESOURCE(
  SYSTEM$REFERENCE('WAREHOUSE', 'marketing_wh', 'SESSION', 'APPLYBUDGET'));
CALL admin.budgets.marketing_budget!ADD_RESOURCE(
  SYSTEM$REFERENCE('DATABASE', 'marketing', 'SESSION', 'APPLYBUDGET'));

CALL admin.budgets.marketing_budget!SET_EMAIL_NOTIFICATIONS(
  'admin_email_int', 'marketing-lead@company.com');
```

```sql
-- Check status
CALL admin.budgets.marketing_budget!GET_SPENDING_LIMIT();
CALL admin.budgets.marketing_budget!GET_SPENDING_HISTORY();
SHOW SNOWFLAKE.CORE.BUDGET;
```

> **⚠️ Gotcha:** Budgets alert based on a *projected* end-of-month spend, so you can get warned before you actually hit the limit.

---

## Catching Anomalies

Snowsight's **Cost Management** page flags cost anomalies automatically. For your own alerts, compare yesterday with the recent average:

```sql
WITH daily AS (
  SELECT usage_date, SUM(credits_used) AS credits
  FROM snowflake.account_usage.metering_daily_history
  WHERE usage_date >= DATEADD(day, -29, CURRENT_DATE())
  GROUP BY 1
),
baseline AS (
  SELECT AVG(credits) AS avg_credits, STDDEV(credits) AS sd_credits
  FROM daily
  WHERE usage_date < DATEADD(day, -1, CURRENT_DATE())
)
SELECT d.usage_date, d.credits, b.avg_credits,
       (d.credits - b.avg_credits) / NULLIF(b.sd_credits, 0) AS z_score
FROM daily d CROSS JOIN baseline b
WHERE d.usage_date = DATEADD(day, -1, CURRENT_DATE());
-- z_score > 3 → something unusual happened yesterday
```

Then drill down by service type and by warehouse to find the cause:

```sql
SELECT service_type, SUM(credits_used) AS credits
FROM snowflake.account_usage.metering_daily_history
WHERE usage_date = DATEADD(day, -1, CURRENT_DATE())
GROUP BY 1 ORDER BY 2 DESC;
```

---

## Spend in Dollars (Org Level)

```sql
-- Needs ORGADMIN (or access to ORGANIZATION_USAGE)
SELECT usage_date, account_name, usage_type, SUM(usage_in_currency) AS cost
FROM snowflake.organization_usage.usage_in_currency_daily
WHERE usage_date > DATEADD(day, -30, CURRENT_DATE())
GROUP BY 1, 2, 3
ORDER BY 1 DESC, cost DESC;
```

## Checklist

- [ ] Account budget activated with a limit and notification email
- [ ] Custom budget per team / major project
- [ ] Daily anomaly alert (z-score or Snowsight anomalies)
- [ ] Monthly cost review in currency, not just credits
