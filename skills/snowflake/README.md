# Snowflake

Notes on running and administering Snowflake.

## Admin

| # | Topic | What's covered |
|:---|:---|:---|
| 01 | [Access Control (RBAC)](admin/01-access-control-rbac.md) | System roles, access vs functional roles, future grants, managed access schemas |
| 02 | [Warehouses & Cost Control](admin/02-warehouses-and-cost-control.md) | Sizing, auto-suspend, multi-cluster, workload isolation, resource monitors |
| 03 | [Users, Auth & Network Security](admin/03-users-auth-network-security.md) | Person vs service users, key-pair auth, MFA, network policies |
| 04 | [Monitoring with ACCOUNT_USAGE](admin/04-monitoring-account-usage.md) | Spend, expensive and slow queries, storage, access audits, alerts |
| 05 | [Time Travel & Fail-safe](admin/05-time-travel-and-failsafe.md) | Retention settings, AT/BEFORE queries, UNDROP, restore-and-swap, Fail-safe costs |
| 06 | [Zero-Copy Cloning](admin/06-zero-copy-cloning.md) | Cloning tables/schemas/dbs, dev envs, blue/green swaps, what doesn't get cloned |
| 07 | [Masking & Row Access Policies](admin/07-masking-and-row-access-policies.md) | Dynamic masking, conditional masking, mapping-table row policies, policy admin role |
| 08 | [Object Tagging & Classification](admin/08-object-tagging-and-classification.md) | Tags, tag-based masking, SYSTEM$CLASSIFY, cost attribution by tag |
| 09 | [Replication & Failover](admin/09-replication-and-failover.md) | Failover groups, client redirect, failover runbook, replication monitoring |
| 10 | [Snowpipe](admin/10-snowpipe.md) | Storage integrations, auto-ingest pipes, PIPE_STATUS, COPY_HISTORY, troubleshooting |
| 11 | [Streams & Tasks](admin/11-streams-and-tasks.md) | CDC streams, staleness, serverless vs warehouse tasks, task graphs, monitoring |
| 12 | [Secure Data Sharing](admin/12-secure-data-sharing.md) | Shares, secure views, consumer setup, reader accounts, listings |
| 13 | [Clustering & Performance](admin/13-clustering-and-performance.md) | Clustering keys, search optimization, query acceleration, caching, serverless costs |
| 14 | [Budgets & Cost Anomalies](admin/14-budgets-and-cost-anomalies.md) | Account and custom budgets, budgets vs resource monitors, anomaly detection, spend in currency |
| 15 | [Dynamic Tables](admin/15-dynamic-tables.md) | Target lag, DOWNSTREAM chaining, incremental vs full refresh, refresh history |
| 16 | [Iceberg Tables](admin/16-iceberg-tables.md) | External volumes, Snowflake-managed vs Glue catalog, refresh, admin gotchas |
| 17 | [Organization Admin](admin/17-organization-admin.md) | ORGADMIN, creating/renaming/dropping accounts, ORGANIZATION_USAGE, account strategy |
| 18 | [External Access & Secrets](admin/18-external-access-and-secrets.md) | Egress network rules, secrets, external access integrations, integration types |
| 19 | [Encryption & Private Connectivity](admin/19-encryption-and-private-connectivity.md) | Key hierarchy, rekeying, Tri-Secret Secure, PrivateLink, private-only network policy |
| 20 | [Security Policies & Trust Center](admin/20-security-policies-and-trust-center.md) | Password and session policies, Trust Center scanners, detection queries |
| 21 | [Parameters](admin/21-parameters.md) | Parameter types and inheritance, day-one settings, QUERY_TAG cost attribution |
| 22 | [Infrastructure as Code](admin/22-infrastructure-as-code.md) | Terraform provider, roles and grants as code, schemachange, guardrails |
| 23 | [Snowpark & Container Services](admin/23-snowpark-and-container-services.md) | Packages, Snowpark-optimized warehouses, compute pools, services, SPCS cost |
| 24 | [Cortex AI Admin](admin/24-cortex-ai-admin.md) | CORTEX_USER role, model allowlist, cross-region inference, token cost monitoring |
| 25 | [Data Quality Monitoring](admin/25-data-quality-monitoring.md) | System and custom DMFs, schedules, expectations, results |
| 26 | [Alerts & Notifications](admin/26-alerts-and-notifications.md) | Email/webhook/queue integrations, alerts, alert history |
| 27 | [Query Troubleshooting](admin/27-query-troubleshooting.md) | Time breakdown, query profile, exploding joins, spilling, locks, killing queries |
| 28 | [Owner's vs Caller's Rights](admin/28-procedures-owners-vs-callers-rights.md) | EXECUTE AS modes, delegating admin actions safely, auditing calls |

## Up Next

- [ ] Snowpark and container services admin
- [ ] Cortex AI features: access control and cost
- [ ] Data quality monitoring (data metric functions)
- [ ] Disaster recovery runbook drill write-up
