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

## Up Next

- [ ] Cost governance: budgets and cost anomaly detection
- [ ] Dynamic tables vs streams + tasks
- [ ] Iceberg tables and external volumes
- [ ] Organization-level admin (ORGADMIN, org usage views)
