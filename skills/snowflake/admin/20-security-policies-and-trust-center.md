# Snowflake Security Policies & Trust Center

> Password and session policies, monitoring for risky activity, and using Trust Center to check the account's security posture.

---

## Password Policies

```sql
USE ROLE SECURITYADMIN;
CREATE PASSWORD POLICY governance.policies.pw_standard
  PASSWORD_MIN_LENGTH        = 14
  PASSWORD_MIN_UPPER_CASE_CHARS = 1
  PASSWORD_MIN_NUMERIC_CHARS = 1
  PASSWORD_MIN_SPECIAL_CHARS = 1
  PASSWORD_MAX_AGE_DAYS      = 90
  PASSWORD_MAX_RETRIES       = 5
  PASSWORD_LOCKOUT_TIME_MINS = 30
  PASSWORD_HISTORY           = 5;

ALTER ACCOUNT SET PASSWORD POLICY governance.policies.pw_standard;
-- A user-level policy overrides the account one
```

> **💡 Note:** Snowflake is phasing out password-only sign-in for human users. Passwords should come with MFA, and should be replaced by SSO where possible (see [03](03-users-auth-network-security.md)).

---

## Session Policies

Control how long idle sessions stay alive.

```sql
CREATE SESSION POLICY governance.policies.session_std
  SESSION_IDLE_TIMEOUT_MINS    = 240   -- drivers, SnowSQL, connectors
  SESSION_UI_IDLE_TIMEOUT_MINS = 30;   -- Snowsight

ALTER ACCOUNT SET SESSION POLICY governance.policies.session_std;

-- Stricter for admins
CREATE SESSION POLICY governance.policies.session_admin
  SESSION_UI_IDLE_TIMEOUT_MINS = 15;
ALTER USER admin_jane SET SESSION POLICY governance.policies.session_admin;
```

---

## Policy Summary

| Policy | Controls | Note |
|:---|:---|:---|
| Network policy | Where logins come from | [03](03-users-auth-network-security.md), [19](19-encryption-and-private-connectivity.md) |
| Authentication policy | Which auth methods / clients, MFA enrollment | [03](03-users-auth-network-security.md) |
| Password policy | Password strength, lockout | This note |
| Session policy | Idle timeouts | This note |
| Masking / row access | What data is visible | [07](07-masking-and-row-access-policies.md) |

```sql
-- Where are policies attached?
SELECT policy_name, policy_kind, ref_entity_name, ref_entity_domain
FROM snowflake.account_usage.policy_references
WHERE policy_kind IN ('PASSWORD_POLICY', 'SESSION_POLICY',
                      'AUTHENTICATION_POLICY', 'NETWORK_POLICY');
```

---

## Trust Center

A Snowsight page (**Monitoring → Trust Center**) that runs **scanner packages** against your account and lists findings by severity.

| Scanner package | Checks |
|:---|:---|
| Security Essentials | MFA, network policies, admin user basics (free, on by default) |
| CIS Benchmarks | CIS Snowflake Foundations Benchmark controls |
| Threat Intelligence | Risky users, unusual logins, suspicious activity |

```sql
-- Findings are also queryable
SELECT *
FROM snowflake.trust_center.findings
ORDER BY created_on DESC
LIMIT 50;
```

> **💡 Tip:** Review Trust Center findings weekly, and enable the CIS package to get a checklist that auditors recognize.

---

## Detection Queries

```sql
-- Who used ACCOUNTADMIN in the last 7 days, and for what?
SELECT user_name, start_time, LEFT(query_text, 120) AS query
FROM snowflake.account_usage.query_history
WHERE role_name = 'ACCOUNTADMIN'
  AND start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- Privilege escalations: new grants of powerful roles
SELECT created_on, grantee_name, role, granted_by
FROM snowflake.account_usage.grants_to_users
WHERE role IN ('ACCOUNTADMIN', 'SECURITYADMIN', 'ORGADMIN')
  AND created_on > DATEADD(day, -30, CURRENT_TIMESTAMP());

-- Logins from new IPs per user (last 24h vs previous 30 days)
SELECT l.user_name, l.client_ip, MIN(l.event_timestamp) AS first_seen
FROM snowflake.account_usage.login_history l
WHERE l.event_timestamp > DATEADD(day, -1, CURRENT_TIMESTAMP())
  AND l.is_success = 'YES'
  AND NOT EXISTS (
    SELECT 1 FROM snowflake.account_usage.login_history h
    WHERE h.user_name = l.user_name AND h.client_ip = l.client_ip
      AND h.event_timestamp BETWEEN DATEADD(day, -31, CURRENT_TIMESTAMP())
                                AND DATEADD(day, -1, CURRENT_TIMESTAMP()))
GROUP BY 1, 2;
```

Wire these into alerts (see [04](04-monitoring-account-usage.md)) or ship `ACCOUNT_USAGE` to your SIEM.

## Checklist

- [ ] Password, session and authentication policies set at account level
- [ ] Stricter session policy for admins
- [ ] Trust Center CIS + Threat Intelligence scanners enabled and reviewed
- [ ] Alerts on ACCOUNTADMIN usage and new admin grants
