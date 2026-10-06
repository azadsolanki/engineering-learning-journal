# Snowflake Alerts & Notification Integrations

> Turning SQL conditions into notifications by email, Slack/Teams webhooks, or cloud queues.

---

## Notification Integrations

| Type | Target |
|:---|:---|
| `EMAIL` | Verified email addresses of Snowflake users |
| `WEBHOOK` | Slack, Microsoft Teams, PagerDuty, any HTTPS endpoint |
| `QUEUE` | AWS SNS, GCP Pub/Sub, Azure Event Grid (also used for task errors) |

### Email

```sql
USE ROLE ACCOUNTADMIN;
CREATE NOTIFICATION INTEGRATION admin_email_int
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('platform-team@company.com');
```

> **⚠️ Gotcha:** Recipients must be **verified** email addresses of users in the account.

### Slack webhook

```sql
CREATE SECRET governance.secrets.slack_webhook
  TYPE = GENERIC_STRING
  SECRET_STRING = 'T000/B000/XXXX';   -- the path part of the Slack webhook URL

CREATE NOTIFICATION INTEGRATION slack_int
  TYPE = WEBHOOK
  ENABLED = TRUE
  WEBHOOK_URL = 'https://hooks.slack.com/services/SNOWFLAKE_WEBHOOK_SECRET'
  WEBHOOK_SECRET = governance.secrets.slack_webhook
  WEBHOOK_BODY_TEMPLATE = '{"text": "SNOWFLAKE_WEBHOOK_MESSAGE"}'
  WEBHOOK_HEADERS = ('Content-Type' = 'application/json');

GRANT USAGE ON INTEGRATION slack_int TO ROLE platform_admin;
```

### Sending a notification

```sql
CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
  SNOWFLAKE.NOTIFICATION.TEXT_PLAIN('Nightly load finished'),
  SNOWFLAKE.NOTIFICATION.INTEGRATION('slack_int'));

-- Email shortcut
CALL SYSTEM$SEND_EMAIL('admin_email_int', 'platform-team@company.com',
  'Subject here', 'Body here');
```

---

## Alerts

An alert runs a condition on a schedule and executes an action when the condition returns rows.

```sql
CREATE OR REPLACE ALERT admin.alerts.failed_tasks
  -- omit WAREHOUSE to run serverless
  SCHEDULE = '15 MINUTE'
  IF (EXISTS (
    SELECT 1
    FROM TABLE(analytics.information_schema.task_history(
      scheduled_time_range_start => SNOWFLAKE.ALERT.LAST_SUCCESSFUL_SCHEDULED_TIME(),
      scheduled_time_range_end   => SNOWFLAKE.ALERT.SCHEDULED_TIME()))
    WHERE state = 'FAILED'
  ))
  THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN('One or more tasks failed in ANALYTICS'),
      SNOWFLAKE.NOTIFICATION.INTEGRATION('slack_int'));

ALTER ALERT admin.alerts.failed_tasks RESUME;   -- alerts are created suspended
```

> **💡 Tip:** Use `LAST_SUCCESSFUL_SCHEDULED_TIME()` and `SCHEDULED_TIME()` as the time window. Each event then fires exactly once, with no gaps or duplicates.

### Ideas for admin alerts

| Alert | Source |
|:---|:---|
| Daily spend anomaly | [14 Budgets](14-budgets-and-cost-anomalies.md) |
| Task / dynamic table failures | [11](11-streams-and-tasks.md), [15](15-dynamic-tables.md) |
| Snowpipe load errors | [10 Snowpipe](10-snowpipe.md) |
| Data quality failures | [25 DMFs](25-data-quality-monitoring.md) |
| New ACCOUNTADMIN grants | [20 Security](20-security-policies-and-trust-center.md) |

> **⚠️ Gotcha:** `ACCOUNT_USAGE` views lag by up to ~3 hours. For near-real-time alerts, use `INFORMATION_SCHEMA` table functions instead.

---

## Operating Alerts

```sql
SHOW ALERTS IN ACCOUNT;
ALTER ALERT admin.alerts.failed_tasks SUSPEND;
EXECUTE ALERT admin.alerts.failed_tasks;   -- run now

-- Did alerts run, and did they fire?
SELECT name, state, condition_query_id, action_query_id, scheduled_time
FROM TABLE(information_schema.alert_history(
  scheduled_time_range_start => DATEADD(day, -1, CURRENT_TIMESTAMP())))
ORDER BY scheduled_time DESC;
```

`state` values: `CONDITION_FALSE` (all good), `TRIGGERED` (action ran), `CONDITION_FAILED` / `ACTION_FAILED` (the alert itself is broken).

## Checklist

- [ ] Email and Slack/Teams integrations set up once, reused everywhere
- [ ] Webhook URLs stored as secrets
- [ ] Core admin alerts in place (spend, failures, security)
- [ ] Alert failures (`CONDITION_FAILED` / `ACTION_FAILED`) monitored too
