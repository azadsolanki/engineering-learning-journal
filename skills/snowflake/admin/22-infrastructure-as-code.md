# Managing Snowflake as Code

> Terraform for account objects and grants, migration tools for schemas, and how to keep humans and code from fighting.

---

## What Goes Where

| Layer | Examples | Tool |
|:---|:---|:---|
| Account infrastructure | Warehouses, databases, roles, users, grants, integrations, policies | **Terraform** (`snowflakedb/snowflake` provider) |
| Schema objects / DDL | Tables, views, procedures | **schemachange**, Snowflake CLI, `CREATE OR ALTER` scripts |
| Transformations | Models, tests | **dbt** (see [`skills/dbt`](../../dbt)) |

> **💡 Rule:** Each object has exactly **one** owner: Terraform, a migration tool, or dbt. Never manage the same object two ways.

---

## Terraform Setup

### Service user for Terraform

```sql
USE ROLE USERADMIN;
CREATE USER svc_terraform TYPE = SERVICE RSA_PUBLIC_KEY = 'MIIBIjANBgkqh...';

USE ROLE SECURITYADMIN;
CREATE ROLE terraform_admin;
GRANT ROLE SYSADMIN      TO ROLE terraform_admin;
GRANT ROLE SECURITYADMIN TO ROLE terraform_admin;   -- needed to manage roles and grants
GRANT ROLE terraform_admin TO USER svc_terraform;
```

### Provider

```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.0"
    }
  }
}

provider "snowflake" {
  organization_name = "myorg"
  account_name      = "prod_us_west"
  user              = "SVC_TERRAFORM"
  role              = "TERRAFORM_ADMIN"
  authenticator     = "SNOWFLAKE_JWT"
  private_key       = file(var.private_key_path)
}
```

---

## Example: Warehouse + Role + Grants

```hcl
resource "snowflake_warehouse" "bi" {
  name           = "BI_WH"
  warehouse_size = "SMALL"
  auto_suspend   = 60
  comment        = "BI dashboards - managed by Terraform"
}

resource "snowflake_account_role" "analyst" {
  name = "ANALYST"
}

resource "snowflake_grant_privileges_to_account_role" "analyst_wh" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.bi.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "analyst_future_tables" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_database        = "ANALYTICS"
    }
  }
}

resource "snowflake_grant_account_role" "analyst_to_sysadmin" {
  role_name        = snowflake_account_role.analyst.name
  parent_role_name = "SYSADMIN"
}
```

> **💡 Tip:** Use modules for repeated patterns, like a `team` module that creates a warehouse, access roles, a functional role and a budget in one go (see [01](01-access-control-rbac.md), [14](14-budgets-and-cost-anomalies.md)).

---

## Importing Existing Objects

```bash
terraform import snowflake_warehouse.bi '"BI_WH"'
terraform plan    # should show no changes once the config matches
```

---

## Schema Migrations

**schemachange**: versioned SQL files, tracked in a change history table.

```
migrations/
├── V1.0.0__create_raw_tables.sql
├── V1.1.0__add_orders_status.sql
└── R__views.sql                 # repeatable, re-run when changed
```

```bash
schemachange deploy -f migrations -c ANALYTICS.SCHEMACHANGE.CHANGE_HISTORY
```

**Declarative alternative:** `CREATE OR ALTER TABLE` / `CREATE OR ALTER VIEW` lets you describe the desired state and run the same script every time.

```bash
snow sql -f deploy/analytics.sql --connection prod   # Snowflake CLI
```

---

## Guardrails

- Run `terraform plan` in CI on every PR, and `apply` only from the main branch.
- Keep state in a remote backend with locking (S3 + DynamoDB, GCS, Terraform Cloud).
- Add a comment like `managed by Terraform` on every object, so people know not to edit it by hand.
- Detect drift with a scheduled `terraform plan`.

## Checklist

- [ ] Dedicated `TYPE = SERVICE` user with key-pair auth for Terraform
- [ ] Clear ownership boundary: Terraform vs migrations vs dbt
- [ ] Remote state with locking
- [ ] Plan on PR, apply on merge, scheduled drift checks
