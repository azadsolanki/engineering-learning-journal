# Cortex AI: Access Control & Cost

> Governing who can call LLM functions in Snowflake, which models they can use, and what it costs.

---

## What's in Cortex

| Feature | What it does | Billed by |
|:---|:---|:---|
| AI SQL functions (`AI_COMPLETE`, `AI_CLASSIFY`, `AI_SENTIMENT`, `SUMMARIZE`...) | LLM calls from SQL | Tokens |
| Cortex Search | Hybrid search service over your text | Serving + indexing |
| Cortex Analyst | Natural language → SQL over a semantic model | Messages |
| Document AI / `AI_EXTRACT` | Extract fields from documents | Pages / tokens |

```sql
SELECT AI_COMPLETE('mistral-large2',
  'Summarize this support ticket in one sentence: ' || ticket_text) AS summary
FROM support.tickets
LIMIT 10;
```

---

## Access Control

All Cortex functions need the `SNOWFLAKE.CORTEX_USER` database role, which is **granted to PUBLIC by default**. That means every user can call LLMs.

```sql
USE ROLE ACCOUNTADMIN;

-- Lock it down: take it away from everyone...
REVOKE DATABASE ROLE snowflake.cortex_user FROM ROLE public;

-- ...and give it only to the roles that need it
CREATE ROLE cortex_users;
GRANT DATABASE ROLE snowflake.cortex_user TO ROLE cortex_users;
GRANT ROLE cortex_users TO ROLE data_science;
```

### Model allowlist

Restrict which models can be used account-wide:

```sql
ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = 'mistral-large2,llama3.1-70b';
-- 'All' (default) or 'None' are also valid
```

### Cross-region inference

Some models aren't hosted in every region. Allowing cross-region calls means **data leaves your region** for processing:

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'AWS_US';   -- or 'ANY_REGION', 'DISABLED'
```

> **⚠️ Gotcha:** Check with legal/compliance before enabling cross-region inference if you have data residency requirements.

---

## Cost Monitoring

```sql
-- Credits by function and model (last 30 days)
SELECT function_name, model_name,
       SUM(tokens)                AS tokens,
       SUM(token_credits)         AS credits
FROM snowflake.account_usage.cortex_functions_usage_history
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY credits DESC;

-- Which queries (and users) spent the most
SELECT q.user_name, c.query_id, c.model_name, c.token_credits
FROM snowflake.account_usage.cortex_functions_query_usage_history c
JOIN snowflake.account_usage.query_history q USING (query_id)
WHERE q.start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY c.token_credits DESC
LIMIT 20;
```

> **💡 Tip:** The classic expensive mistake is running `AI_COMPLETE` over a whole multi-million-row table with a large model. Test on `LIMIT 100` first, then multiply the cost before running it on everything.

---

## Cost-Saving Patterns

- Use the **smallest model that works**. Task-specific functions (`AI_SENTIMENT`, `AI_CLASSIFY`) are usually cheaper than a general `AI_COMPLETE` prompt.
- **Cache results** in a table instead of re-calling the LLM in views that get queried repeatedly.
- Only process **new rows** incrementally, using streams or dynamic tables (see [11](11-streams-and-tasks.md), [15](15-dynamic-tables.md)).
- Put Cortex workloads in their own warehouse and budget (see [14](14-budgets-and-cost-anomalies.md)).

## Checklist

- [ ] `CORTEX_USER` revoked from PUBLIC and granted to specific roles
- [ ] Model allowlist set
- [ ] Cross-region inference decision documented
- [ ] Cortex credits monitored by user and model
