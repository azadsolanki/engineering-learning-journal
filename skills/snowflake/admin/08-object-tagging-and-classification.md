# Snowflake Object Tagging & Data Classification

> Labeling objects for governance and cost tracking, finding sensitive data, and masking by tag.

---

## Why Tags?

Tags are key/value labels you can attach to accounts, warehouses, databases, schemas, tables and columns.

| Use | Example |
|:---|:---|
| Sensitive data tracking | `pii = 'email'` on a column |
| Cost attribution | `cost_center = 'marketing'` on a warehouse |
| Ownership | `owner_team = 'data-platform'` on a database |
| Tag-based masking | Every column tagged `pii` gets masked automatically |

---

## Creating & Applying Tags

```sql
USE ROLE policy_admin;
CREATE TAG governance.tags.pii
  ALLOWED_VALUES 'email', 'phone', 'ssn', 'name', 'address'
  COMMENT = 'Personally identifiable information';

CREATE TAG governance.tags.cost_center;

ALTER TABLE analytics.crm.customers
  MODIFY COLUMN email SET TAG governance.tags.pii = 'email';

ALTER WAREHOUSE bi_wh SET TAG governance.tags.cost_center = 'analytics';
```

Tags are **inherited**. A tag on a schema applies to its tables and columns unless they override it.

```sql
-- Grant tag management centrally
GRANT APPLY TAG ON ACCOUNT TO ROLE policy_admin;
```

---

## Tag-Based Masking

Attach a masking policy to a **tag** instead of to individual columns. Any column with that tag is masked, including new ones.

```sql
CREATE MASKING POLICY governance.policies.mask_pii_string
  AS (val STRING) RETURNS STRING ->
  CASE WHEN IS_ROLE_IN_SESSION('PII_READER') THEN val ELSE '***MASKED***' END;

ALTER TAG governance.tags.pii SET MASKING POLICY governance.policies.mask_pii_string;
```

> **💡 Tip:** A tag can have one masking policy *per data type*. Add policies for `NUMBER`, `DATE`, etc. if tagged columns aren't all strings.

> **⚠️ Gotcha:** A masking policy set directly on a column takes precedence over a tag-based policy.

---

## Automatic Classification

Snowflake can scan tables and suggest (or apply) the system tags `SNOWFLAKE.CORE.SEMANTIC_CATEGORY` and `SNOWFLAKE.CORE.PRIVACY_CATEGORY`.

```sql
-- Classify one table and apply the tags automatically
CALL SYSTEM$CLASSIFY('analytics.crm.customers', {'auto_tag': true});

-- See results
SELECT SYSTEM$GET_TAG('SNOWFLAKE.CORE.SEMANTIC_CATEGORY',
                      'analytics.crm.customers.email', 'COLUMN');
```

For ongoing coverage, look at **classification profiles**, which classify schemas or databases automatically on a schedule.

---

## Reporting

```sql
-- All tagged columns in the account
SELECT tag_name, tag_value, object_database, object_name, column_name
FROM snowflake.account_usage.tag_references
WHERE domain = 'COLUMN'
ORDER BY tag_name, object_name;

-- Credits by cost_center tag on warehouses (last 30 days)
SELECT t.tag_value AS cost_center,
       SUM(m.credits_used) AS credits
FROM snowflake.account_usage.warehouse_metering_history m
JOIN snowflake.account_usage.tag_references t
  ON t.object_name = m.warehouse_name
 AND t.domain = 'WAREHOUSE'
 AND t.tag_name = 'COST_CENTER'
WHERE m.start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY credits DESC;
```

## Checklist

- [ ] A small, controlled set of tags with `ALLOWED_VALUES`
- [ ] PII columns tagged (manually or via classification)
- [ ] Tag-based masking on the `pii` tag
- [ ] Every warehouse tagged with a cost center
