# Snowflake Users, Authentication & Network Security

> Creating users, service accounts with key-pair auth, MFA, and restricting where logins come from.

---

## Creating Users

```sql
USE ROLE USERADMIN;
CREATE USER jdoe
  LOGIN_NAME        = 'jdoe@company.com'
  EMAIL             = 'jdoe@company.com'
  DEFAULT_ROLE      = analyst
  DEFAULT_WAREHOUSE = bi_wh
  MUST_CHANGE_PASSWORD = TRUE
  PASSWORD          = '<temp-password>';

GRANT ROLE analyst TO USER jdoe;   -- DEFAULT_ROLE does not grant the role!
```

> **⚠️ Gotcha:** Setting `DEFAULT_ROLE` does not grant it. Always run the `GRANT ROLE` too.

### User types

| `TYPE` | Use for | Notes |
|:---|:---|:---|
| `PERSON` | Humans | SSO / password + MFA |
| `SERVICE` | Apps, pipelines, dbt, Airflow | No password or MFA; key-pair or OAuth only |
| `LEGACY_SERVICE` | Old integrations still using passwords | Being phased out — migrate off |

---

## Service Accounts with Key-Pair Auth

```bash
# Generate an encrypted private key and the public key
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes256 -inform PEM -out rsa_key.p8
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

```sql
CREATE USER svc_airflow
  TYPE              = SERVICE
  DEFAULT_ROLE      = data_engineer
  DEFAULT_WAREHOUSE = transform_wh
  RSA_PUBLIC_KEY    = 'MIIBIjANBgkqh...';   -- body of rsa_key.pub, no header/footer

-- Rotation: set key 2, move clients over, then drop key 1
ALTER USER svc_airflow SET RSA_PUBLIC_KEY_2 = 'MIIBIjANBgkqh...';
ALTER USER svc_airflow UNSET RSA_PUBLIC_KEY;

DESC USER svc_airflow;   -- check RSA_PUBLIC_KEY_FP fingerprints
```

---

## MFA & SSO

- Humans should log in through **SSO** (SAML2 security integration with Okta/Azure AD) or password **+ MFA**.
- Enforce MFA with an **authentication policy**:

```sql
CREATE AUTHENTICATION POLICY require_mfa
  MFA_ENROLLMENT = REQUIRED
  CLIENT_TYPES   = ('SNOWFLAKE_UI', 'SNOWSQL', 'DRIVERS');

ALTER ACCOUNT SET AUTHENTICATION POLICY require_mfa;
```

- **SCIM** provisioning from the IdP keeps users/roles in sync automatically, so offboarding happens in one place.

---

## Network Policies & Rules

Restrict which IPs can connect. Modern approach: define **network rules**, then reference them in a policy.

```sql
USE ROLE SECURITYADMIN;
CREATE NETWORK RULE corp_vpn_ips
  TYPE = IPV4  MODE = INGRESS
  VALUE_LIST = ('203.0.113.0/24');

CREATE NETWORK POLICY corp_only
  ALLOWED_NETWORK_RULE_LIST = ('corp_vpn_ips');

-- Apply to a single user first (safer), then the account
ALTER USER svc_airflow SET NETWORK_POLICY = corp_only;
ALTER ACCOUNT SET NETWORK_POLICY = corp_only;
```

> **⚠️ Lockout warning:** Before applying at account level, confirm your *current* IP is allowed. A user-level policy overrides the account-level one.

---

## Day-to-Day Commands

```sql
SHOW USERS;
DESC USER jdoe;
ALTER USER jdoe SET DISABLED = TRUE;          -- offboarding
ALTER USER jdoe RESET PASSWORD;               -- returns a reset URL
ALTER USER jdoe SET MINS_TO_UNLOCK = 0;       -- unlock after failed logins

-- Failed logins in the last day
SELECT user_name, client_ip, error_message, event_timestamp
FROM snowflake.account_usage.login_history
WHERE is_success = 'NO'
  AND event_timestamp > DATEADD(day, -1, CURRENT_TIMESTAMP())
ORDER BY event_timestamp DESC;
```

## Checklist

- [ ] All humans on SSO or MFA
- [ ] All pipelines use `TYPE = SERVICE` + key-pair (no passwords)
- [ ] Network policy applied to service users at minimum
- [ ] Offboarding disables users (via SCIM or runbook)
