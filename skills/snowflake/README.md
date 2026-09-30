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

## Up Next

- [ ] Data protection: Time Travel, Fail-safe, zero-copy cloning
- [ ] Data governance: masking and row access policies, tags
- [ ] Replication and failover
- [ ] Snowpipe and tasks
