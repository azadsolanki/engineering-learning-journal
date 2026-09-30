# Snowflake Masking & Row Access Policies

> Column-level and row-level security that follows the data, whatever role queries it. (Enterprise+)

---

## Two Policy Types

| Policy | Controls | Returns |
|:---|:---|:---|
| **Masking policy** | What a user sees *in a column* | The (possibly masked) value |
| **Row access policy** | Which *rows* a user sees | `TRUE` (show row) / `FALSE` (hide row) |

Policies are evaluated at query time, so the same table serves every role.

---

## Masking Policies

```sql
USE ROLE SECURITYADMIN;   -- or a dedicated policy_admin role
CREATE SCHEMA governance.policies;

CREATE MASKING POLICY governance.policies.mask_email
  AS (val STRING) RETURNS STRING ->
  CASE
    WHEN IS_ROLE_IN_SESSION('PII_READER') THEN val
    WHEN IS_ROLE_IN_SESSION('ANALYST')    THEN REGEXP_REPLACE(val, '.+@', '****@')
    ELSE '********'
  END;

ALTER TABLE analytics.crm.customers
  MODIFY COLUMN email SET MASKING POLICY governance.policies.mask_email;
```

| Role | Sees |
|:---|:---|
| PII_READER | `jane.doe@acme.com` |
| ANALYST | `****@acme.com` |
| Everyone else | `********` |

> **💡 Tip:** Use `IS_ROLE_IN_SESSION()` instead of `CURRENT_ROLE() IN (...)`. It respects role inheritance and secondary roles.

### Conditional masking

Mask one column based on another:

```sql
CREATE MASKING POLICY governance.policies.mask_ssn_unless_consented
  AS (ssn STRING, consent BOOLEAN) RETURNS STRING ->
  CASE WHEN consent OR IS_ROLE_IN_SESSION('PII_READER') THEN ssn ELSE '***-**-****' END;

ALTER TABLE customers MODIFY COLUMN ssn
  SET MASKING POLICY governance.policies.mask_ssn_unless_consented USING (ssn, consent_flag);
```

---

## Row Access Policies

Typical pattern: a **mapping table** says which role can see which values.

```sql
CREATE TABLE governance.policies.region_access (role_name STRING, region STRING);
INSERT INTO governance.policies.region_access VALUES
  ('SALES_EMEA', 'EMEA'), ('SALES_US', 'US');

CREATE ROW ACCESS POLICY governance.policies.rap_region
  AS (sales_region STRING) RETURNS BOOLEAN ->
  IS_ROLE_IN_SESSION('SALES_ADMIN')
  OR EXISTS (
    SELECT 1 FROM governance.policies.region_access m
    WHERE IS_ROLE_IN_SESSION(m.role_name)
      AND m.region = sales_region
  );

ALTER TABLE analytics.sales.orders
  ADD ROW ACCESS POLICY governance.policies.rap_region ON (region);
```

> **⚠️ Gotcha:** A table can have only **one** row access policy, and a column only **one** masking policy. Design them centrally.

---

## Governance Setup

Keep policy management separate from object ownership:

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE policy_admin;
GRANT CREATE MASKING POLICY, CREATE ROW ACCESS POLICY
  ON SCHEMA governance.policies TO ROLE policy_admin;
GRANT APPLY MASKING POLICY    ON ACCOUNT TO ROLE policy_admin;
GRANT APPLY ROW ACCESS POLICY ON ACCOUNT TO ROLE policy_admin;
```

---

## Auditing

```sql
-- Where is a policy attached?
SELECT *
FROM TABLE(governance.information_schema.policy_references(
  policy_name => 'governance.policies.mask_email'));

-- All policy attachments in the account
SELECT policy_name, policy_kind, ref_database_name, ref_entity_name, ref_column_name
FROM snowflake.account_usage.policy_references
ORDER BY policy_kind, policy_name;
```

## Checklist

- [ ] Policies live in one governance schema, owned by a policy admin role
- [ ] `IS_ROLE_IN_SESSION()` used in policy bodies
- [ ] Mapping tables used instead of hard-coded role lists
- [ ] Policy coverage reviewed with `POLICY_REFERENCES`
