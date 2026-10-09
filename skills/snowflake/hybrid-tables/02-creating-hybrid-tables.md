# Creating Hybrid Tables

> Keys, constraints, secondary indexes, and loading data without tripping over the rules.

---

## Prerequisite

You need a **running warehouse** set as the current warehouse for the session to create a hybrid table.

---

## Basic Table

```sql
CREATE OR REPLACE HYBRID TABLE app.core.customers (
  customer_id NUMBER       PRIMARY KEY AUTOINCREMENT,
  email       VARCHAR(255) NOT NULL UNIQUE,
  full_name   VARCHAR(200),
  region      VARCHAR(20)  NOT NULL,
  created_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

- `PRIMARY KEY` is **mandatory**.
- `UNIQUE`, `NOT NULL` and `FOREIGN KEY` are **enforced**. A duplicate email fails the insert.
- `NOT ENFORCED` on PK / UNIQUE / FK raises an "invalid constraint property" error.

---

## Foreign Keys

```sql
CREATE OR REPLACE HYBRID TABLE app.core.orders (
  order_id    NUMBER PRIMARY KEY AUTOINCREMENT,
  customer_id NUMBER NOT NULL,
  status      VARCHAR(20) NOT NULL,
  amount      NUMBER(12,2),
  updated_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES app.core.customers (customer_id),
  INDEX idx_orders_customer (customer_id),
  INDEX idx_orders_status (status) INCLUDE (amount)
);
```

> **⚠️ Gotcha:** All hybrid tables in one transaction (and FK relationships) must be in the **same database**.

---

## Secondary Indexes

Indexes are updated **synchronously** on every write: great for reads, but each index adds write cost.

```sql
-- Inline at creation (above) or afterwards:
CREATE INDEX idx_customers_region ON app.core.customers (region);

SHOW INDEXES IN TABLE app.core.customers;
DROP INDEX app.core.customers.idx_customers_region;
```

| Rule | Detail |
|:---|:---|
| Can't alter an index | Drop and recreate it to change columns |
| Some types can't be indexed | `VARIANT`, `ARRAY`, `OBJECT`, `GEOGRAPHY`, `GEOMETRY`, `VECTOR` can't be PK or indexed columns |
| No collations on indexed columns | Use plain `VARCHAR` |
| `INCLUDE (...)` columns | Covering index: answers the query without touching the base row |
| Using an index | Needs `SELECT` on the table |

> **💡 Tip:** Index the columns your app filters by (`WHERE customer_id = ?`). Don't index "just in case". Every index slows inserts and updates.

---

## Loading Data

Bulk-load paths: **CTAS**, `COPY INTO`, and `INSERT ... SELECT`.

```sql
-- CTAS: declare the PK in the column list
CREATE OR REPLACE HYBRID TABLE app.core.customers_hist (
  customer_id NUMBER PRIMARY KEY,
  email       VARCHAR(255),
  region      VARCHAR(20)
)
AS SELECT customer_id, email, region FROM analytics.crm.customers;
```

| Situation | Use |
|:---|:---|
| New table from a query | CTAS (no FOREIGN KEY in CTAS; add it after with `ALTER TABLE`) |
| Files in a stage | `COPY INTO` (`ON_ERROR = ABORT_STATEMENT` only) |
| Table has a CHECK constraint | `INSERT INTO ... SELECT` (COPY fails with CHECK) |
| Table has FK **and** CHECK | `INSERT INTO ... SELECT` |
| Continuous ingestion | Not Snowpipe (unsupported). Use app inserts or scheduled `INSERT ... SELECT` |

> **⚠️ Gotcha:** "The value is too long for index" during loads means an index covers wide columns. Index fewer or narrower columns, or move wide columns into `INCLUDE`.

---

## Other Rules

- Hybrid tables can't be **temporary or transient**, and can't live in transient schemas or databases.
- `CHECK` constraints can only be defined at **creation**.
- Avoid the `UUID` type entirely (not supported in any column).

## Checklist

- [ ] PK chosen for the app's main lookup path
- [ ] Only the indexes the app's queries actually need
- [ ] FKs within one database
- [ ] Load method matches the table's constraints

**Docs:** [Create hybrid tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-create)
