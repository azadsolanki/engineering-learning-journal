# Hybrid Tables Lab: Transactional Patterns

> Hands-on SQL that shows what makes hybrid tables different: enforced constraints, row-level locking, and joining with analytical tables.

> **⚠️ Requires a paid account** in an AWS or Azure commercial region. Hybrid tables aren't available on trial accounts ([03](03-limitations-and-availability.md)).

---

## Setup

```sql
USE ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS lab_wh WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60;
USE WAREHOUSE lab_wh;                 -- a running warehouse is required to create hybrid tables

CREATE DATABASE IF NOT EXISTS unistore_lab;
CREATE SCHEMA IF NOT EXISTS unistore_lab.app;
USE SCHEMA unistore_lab.app;

CREATE OR REPLACE HYBRID TABLE customers (
  customer_id NUMBER PRIMARY KEY,
  email       VARCHAR(255) NOT NULL UNIQUE,
  region      VARCHAR(20)  NOT NULL
);

CREATE OR REPLACE HYBRID TABLE orders (
  order_id    NUMBER PRIMARY KEY AUTOINCREMENT,
  customer_id NUMBER NOT NULL,
  status      VARCHAR(20) NOT NULL,
  amount      NUMBER(12,2),
  CONSTRAINT fk_cust FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  INDEX idx_orders_customer (customer_id)
);

INSERT INTO customers VALUES
  (1, 'ana@example.com', 'EMEA'),
  (2, 'raj@example.com', 'APAC');
INSERT INTO orders (customer_id, status, amount) VALUES
  (1, 'NEW', 120.00), (1, 'NEW', 80.50), (2, 'NEW', 42.00);
```

---

## Exercise 1: Constraints Are Enforced

```sql
-- Duplicate primary key → fails
INSERT INTO customers VALUES (1, 'other@example.com', 'US');

-- Duplicate UNIQUE email → fails
INSERT INTO customers VALUES (3, 'ana@example.com', 'US');

-- Order for a customer that doesn't exist → fails (foreign key)
INSERT INTO orders (customer_id, status, amount) VALUES (999, 'NEW', 10);

-- Delete a customer who still has orders → fails (foreign key)
DELETE FROM customers WHERE customer_id = 1;
```

**Compare:** run the same duplicate insert against a *standard* table with a declared PK. It succeeds, because standard tables don't enforce PKs.

---

## Exercise 2: Row-Level Locking

Open **two worksheets** (two sessions).

| Step | Session A | Session B |
|:---|:---|:---|
| 1 | `BEGIN;` | |
| 2 | `UPDATE orders SET status = 'PAID' WHERE order_id = 1;` | |
| 3 | | `UPDATE orders SET status = 'SHIPPED' WHERE order_id = 2;` → **succeeds immediately** (different row) |
| 4 | | `UPDATE orders SET status = 'CANCELLED' WHERE order_id = 1;` → **waits** (same row) |
| 5 | `COMMIT;` | Step 4 now completes |

With a standard table, step 3 would also wait, because locks are taken at the partition/table level.

```sql
SHOW LOCKS IN ACCOUNT;          -- run during step 4 to see the waiting lock
SHOW TRANSACTIONS IN ACCOUNT;
```

---

## Exercise 3: Pipeline Control Table

A practical admin pattern: track job high-water marks with single-row upserts.

```sql
CREATE OR REPLACE HYBRID TABLE job_state (
  job_name       VARCHAR(100) PRIMARY KEY,
  high_watermark TIMESTAMP_NTZ,
  last_status    VARCHAR(20),
  updated_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

MERGE INTO job_state t
USING (SELECT 'load_orders' AS job_name, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS hw) s
  ON t.job_name = s.job_name
WHEN MATCHED THEN UPDATE SET high_watermark = s.hw, last_status = 'OK',
                             updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (job_name, high_watermark, last_status)
                      VALUES (s.job_name, s.hw, 'OK');

SELECT * FROM job_state WHERE job_name = 'load_orders';   -- PK lookup
```

Many jobs can update their own rows at the same time without blocking each other.

---

## Exercise 4: Join with Analytical Data

Hybrid and standard tables can be joined in one query.

```sql
CREATE OR REPLACE TABLE region_targets (region VARCHAR(20), monthly_target NUMBER);
INSERT INTO region_targets VALUES ('EMEA', 500), ('APAC', 300);

SELECT c.region,
       SUM(o.amount)         AS revenue,
       ANY_VALUE(t.monthly_target) AS target
FROM orders o
JOIN customers c      ON o.customer_id = c.customer_id   -- hybrid ⨝ hybrid
JOIN region_targets t ON t.region = c.region             -- hybrid ⨝ standard
GROUP BY c.region;
```

---

## Exercise 5: Check What It Costs

```sql
SELECT table_name, bytes
FROM snowflake.account_usage.hybrid_tables
WHERE table_catalog = 'UNISTORE_LAB' AND deleted IS NULL;
```

`ACCOUNT_USAGE` lags, so give it a few hours. See [04 Cost & Monitoring](04-cost-and-monitoring.md).

---

## Cleanup

```sql
DROP DATABASE unistore_lab;   -- remember: no UNDROP for hybrid tables
DROP WAREHOUSE lab_wh;
```

## What This Lab Shows

- [ ] PK, UNIQUE and FK are enforced, unlike on standard tables
- [ ] Concurrent updates to **different rows** don't block each other
- [ ] Single-row upserts work well for control/state tables
- [ ] Hybrid and standard tables join in ordinary SQL
