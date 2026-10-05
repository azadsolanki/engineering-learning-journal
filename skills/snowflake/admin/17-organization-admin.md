# Snowflake Organization-Level Admin

> Managing multiple accounts with ORGADMIN: creating accounts, naming, org-wide usage and billing.

---

## The Hierarchy

```
Organization (myorg)
├── prod_us_west     (Enterprise, AWS us-west-2)
├── dr_us_east       (Enterprise, AWS us-east-1)
├── dev              (Standard)
└── partner_reader   (reader account, owned by prod_us_west)
```

- Account URL: `https://myorg-prod_us_west.snowflakecomputing.com` (org name + account name)
- The legacy **account locator** URL still works, but prefer the org-based name.

| Role | Scope |
|:---|:---|
| **ORGADMIN** | Accounts in the org, org-wide usage, replication enablement |
| **GLOBALORGADMIN** | Newer: org-level admin role in a dedicated *organization account* |
| **ACCOUNTADMIN** | Everything *inside* one account |

> **💡 Tip:** Enable ORGADMIN in one account only (usually prod or a dedicated admin account), and grant it to as few people as possible.

---

## Creating & Managing Accounts

```sql
USE ROLE ORGADMIN;

CREATE ACCOUNT dev
  ADMIN_NAME    = 'dev_admin'
  ADMIN_RSA_PUBLIC_KEY = 'MIIBIjANBgkqh...'   -- or ADMIN_PASSWORD
  EMAIL         = 'platform-team@company.com'
  EDITION       = STANDARD
  REGION        = AWS_US_WEST_2
  COMMENT       = 'Developer sandbox';

SHOW ACCOUNTS;
SHOW REGIONS;

ALTER ACCOUNT dev RENAME TO sandbox;          -- the old URL keeps working for a while
ALTER ACCOUNT sandbox SET IS_ORG_ADMIN = TRUE;  -- enable ORGADMIN in that account
```

### Dropping (with a safety net)

```sql
DROP ACCOUNT sandbox GRACE_PERIOD_IN_DAYS = 14;
UNDROP ACCOUNT sandbox;    -- possible during the grace period
```

---

## Org-Wide Usage (ORGANIZATION_USAGE)

Like ACCOUNT_USAGE, but across every account. Higher latency (up to ~24h for some views).

```sql
-- Credits by account and service (last 30 days)
SELECT account_name, service_type, SUM(credits_used) AS credits
FROM snowflake.organization_usage.metering_daily_history
WHERE usage_date > DATEADD(day, -30, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY credits DESC;

-- Contract balance remaining
SELECT date, free_usage_balance, capacity_balance, on_demand_consumption_balance
FROM snowflake.organization_usage.remaining_balance_daily
ORDER BY date DESC
LIMIT 7;

-- Storage by account
SELECT account_name, usage_date, AVG(average_bytes) / POWER(1024, 4) AS tb
FROM snowflake.organization_usage.storage_daily_history
WHERE usage_date > DATEADD(day, -7, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY 2 DESC, 3 DESC;
```

---

## Account Strategy Tips

| Pattern | When |
|:---|:---|
| One account, separate databases for dev/prod | Small teams; simplest grants and sharing |
| Separate prod and non-prod accounts | Stronger isolation; different editions to save money |
| Account per region | Data residency rules, or low latency for regional users |
| Dedicated DR account | Failover groups (see [09](09-replication-and-failover.md)) |

> **⚠️ Gotcha:** Objects (roles, users, warehouses) are per account. More accounts means duplicating setup, so automate it with IaC (see [22](22-infrastructure-as-code.md)).

## Checklist

- [ ] ORGADMIN enabled in a single account, granted to 1–2 people
- [ ] Every account has an owner email and comment
- [ ] Org-wide spend reviewed monthly from ORGANIZATION_USAGE
- [ ] Account creation scripted, not done by hand
