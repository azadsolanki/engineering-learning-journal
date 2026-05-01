# SCD Type 2 Interview Preparation Guide

## Quick 30-Second Answer

**"What is SCD Type 2?"**

> "SCD Type 2 is a data warehousing technique that preserves historical data by creating new records when dimensions change, rather than updating existing ones. We use a surrogate key, effective and expiration dates, and a current flag to track versions. This allows us to maintain a complete audit trail and perform point-in-time analysis."

---

## Common Interview Questions & Answers

### Q1: What is the difference between SCD Type 1, Type 2, and Type 3?

**Answer:**
- **Type 1**: Overwrites old data. No history kept. Simple but loses information.
- **Type 2**: Adds new records for changes. Full history preserved. Most commonly used.
- **Type 3**: Adds new columns (e.g., previous_value, current_value). Limited history (only 1-2 versions).

**Example:**
```
Type 1: Update name = 'John Smith Jr' (old value lost)
Type 2: Insert new row with new name (both versions kept)
Type 3: Add column previous_name = 'John Smith' (limited to 2 versions)
```

---

### Q2: Explain the table structure for SCD Type 2

**Answer:**
```sql
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,     -- Surrogate key (unique per version)
    customer_id VARCHAR(20),             -- Natural/Business key (same across versions)
    customer_name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50),
    effective_date DATE NOT NULL,        -- When this version became active
    expiration_date DATE,                -- When expired (NULL = current)
    is_current BOOLEAN DEFAULT TRUE      -- Quick flag for active record
);
```

**Key points to mention:**
- Surrogate key vs Natural key
- Effective/Expiration dates for temporal tracking
- is_current flag for performance
- NULL expiration_date means current/active record

---

### Q3: How do you implement SCD Type 2? Walk me through the process.

**Answer:**

**Step 1: Detect Changes**
```sql
-- Find records that changed
SELECT s.customer_id
FROM staging s
INNER JOIN dim_customer d 
    ON s.customer_id = d.customer_id 
    AND d.is_current = TRUE
WHERE s.email != d.email OR s.city != d.city;
```

**Step 2: Close Old Records**
```sql
UPDATE dim_customer 
SET 
    expiration_date = CURRENT_DATE,
    is_current = FALSE
WHERE customer_id IN (changed_customers)
  AND is_current = TRUE;
```

**Step 3: Insert New Versions**
```sql
INSERT INTO dim_customer 
    (customer_id, customer_name, email, city, effective_date, is_current)
SELECT customer_id, customer_name, email, city, CURRENT_DATE, TRUE
FROM staging
WHERE customer_id IN (changed_customers);
```

**Step 4: Insert New Records**
```sql
INSERT INTO dim_customer 
    (customer_id, customer_name, email, city, effective_date, is_current)
SELECT customer_id, customer_name, email, city, CURRENT_DATE, TRUE
FROM staging s
WHERE NOT EXISTS (
    SELECT 1 FROM dim_customer d WHERE d.customer_id = s.customer_id
);
```

---

### Q4: How do you identify changes in SCD Type 2?

**Answer:**
I typically use **LEFT JOIN with explicit column comparison**:

```sql
SELECT s.customer_id, 'CHANGED' as change_type
FROM staging s
INNER JOIN dim_customer d 
    ON s.customer_id = d.customer_id 
    AND d.is_current = TRUE
WHERE s.email != d.email 
   OR s.phone != d.phone
   OR s.city != d.city;
```

**Alternative: Hash-based detection** (for tables with many columns):
```sql
-- In staging
UPDATE staging SET record_hash = MD5(email || phone || city);

-- Detect changes
WHERE staging.record_hash != dim_customer.record_hash
```

**Mention:** Hash approach is faster for wide tables but requires hash calculation overhead.

---

### Q5: What is the difference between surrogate key and natural key?

**Answer:**

| Aspect | Surrogate Key | Natural Key |
|--------|---------------|-------------|
| **Purpose** | Unique identifier for each version | Business identifier |
| **Uniqueness** | Unique across all records | Repeats across versions |
| **Example** | customer_key: 1, 2, 3 | customer_id: 'C001', 'C001', 'C001' |
| **Used in FK** | ✅ Yes (in fact tables) | ❌ No |
| **Changes** | Never changes | Stays constant across versions |

**Example:**
```
customer_key | customer_id | email           | is_current
-------------|-------------|-----------------|------------
1            | C001        | old@email.com   | FALSE
2            | C001        | new@email.com   | TRUE
```
- customer_key (1, 2) = Surrogate keys (unique)
- customer_id (C001) = Natural key (same for both versions)

---

### Q6: How do you query current vs historical data?

**Answer:**

**Get Current Records:**
```sql
SELECT * FROM dim_customer WHERE is_current = TRUE;
-- OR
SELECT * FROM dim_customer WHERE expiration_date IS NULL;
```

**Get All History for a Customer:**
```sql
SELECT * FROM dim_customer 
WHERE customer_id = 'C001'
ORDER BY effective_date;
```

**Point-in-Time Query (as of specific date):**
```sql
SELECT * FROM dim_customer 
WHERE customer_id = 'C001'
  AND effective_date <= '2024-01-15'
  AND (expiration_date > '2024-01-15' OR expiration_date IS NULL);
```

---

### Q7: How do fact tables join with SCD Type 2 dimensions?

**Answer:**

**Fact tables use the SURROGATE KEY, not the natural key:**

```sql
CREATE TABLE fact_orders (
    order_id VARCHAR(20),
    customer_key INTEGER,  -- References surrogate key
    order_date DATE,
    amount DECIMAL(10,2),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key)
);

-- Join to get customer info at time of order
SELECT 
    o.order_id,
    o.order_date,
    c.customer_name,
    c.city
FROM fact_orders o
JOIN dim_customer c ON o.customer_key = c.customer_key;
```

**Why surrogate key?**
- Preserves the exact customer state at transaction time
- If customer moved from NYC to LA, old orders still show NYC
- Maintains referential integrity

---

### Q8: What are the advantages and disadvantages of SCD Type 2?

**Answer:**

**Advantages:**
✅ Complete historical audit trail  
✅ Point-in-time reporting accuracy  
✅ Supports temporal analysis  
✅ No data loss  
✅ Regulatory compliance (SOX, GDPR)

**Disadvantages:**
❌ Increased storage requirements  
❌ More complex queries  
❌ Slower query performance on large tables  
❌ ETL complexity increases  
❌ Potential data quality issues if not handled properly

**When to use:**
- When history matters (customer addresses, pricing, employee roles)
- Regulatory requirements
- Financial reporting
- Audit requirements

**When NOT to use:**
- Data corrections (use Type 1)
- Low-value attributes that change frequently
- Real-time operational systems

---

### Q9: How do you handle NULL values in change detection?

**Answer:**

**Problem:** `NULL != NULL` returns NULL (not TRUE), so changes might be missed.

**Solution:** Use `IS DISTINCT FROM` or `COALESCE`

```sql
-- Option 1: IS DISTINCT FROM (PostgreSQL)
WHERE s.phone IS DISTINCT FROM d.phone

-- Option 2: COALESCE
WHERE COALESCE(s.phone, '') != COALESCE(d.phone, '')

-- Option 3: Explicit NULL handling
WHERE (s.phone != d.phone) 
   OR (s.phone IS NULL AND d.phone IS NOT NULL)
   OR (s.phone IS NOT NULL AND d.phone IS NULL)
```

---

### Q10: How would you optimize SCD Type 2 performance?

**Answer:**

**1. Indexing Strategy:**
```sql
-- Index on natural key
CREATE INDEX idx_customer_id ON dim_customer(customer_id);

-- Partial index for current records (PostgreSQL)
CREATE INDEX idx_current 
ON dim_customer(customer_id) WHERE is_current = TRUE;

-- Index on dates for point-in-time queries
CREATE INDEX idx_dates 
ON dim_customer(effective_date, expiration_date);
```

**2. Partitioning:**
```sql
-- Partition by year
CREATE TABLE dim_customer_2024 
PARTITION OF dim_customer 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

**3. Incremental Loading:**
- Only process changed records (CDC - Change Data Capture)
- Use staging tables to minimize locks
- Batch updates during off-peak hours

**4. Query Optimization:**
- Use `is_current` flag instead of checking `expiration_date IS NULL`
- Avoid full table scans with proper WHERE clauses
- Use EXPLAIN ANALYZE to identify bottlenecks

---

### Q11: What is a slowly changing dimension?

**Answer:**

A slowly changing dimension (SCD) is a dimension that contains relatively stable data but can change over time. The "slowly" means changes happen infrequently compared to fact table transactions.

**Examples:**
- Customer addresses (change when moving)
- Employee departments (change on promotion/transfer)
- Product prices (change periodically)
- Supplier contact information

**Not SCD examples:**
- Transaction dates (never change)
- Transaction amounts (never change)
- Stock prices (change too frequently - use fact table instead)

---

### Q12: Can you write a complete SCD Type 2 stored procedure?

**Answer:**

```sql
CREATE OR REPLACE PROCEDURE upsert_dim_customer()
LANGUAGE plpgsql
AS $$
BEGIN
    -- Step 1: Expire changed records
    UPDATE dim_customer d
    SET 
        expiration_date = CURRENT_DATE,
        is_current = FALSE
    FROM staging_customer s
    WHERE d.customer_id = s.customer_id
      AND d.is_current = TRUE
      AND (
          d.customer_name IS DISTINCT FROM s.customer_name OR
          d.email IS DISTINCT FROM s.email OR
          d.city IS DISTINCT FROM s.city
      );

    -- Step 2: Insert new versions
    INSERT INTO dim_customer 
        (customer_id, customer_name, email, city, 
         effective_date, expiration_date, is_current)
    SELECT 
        s.customer_id, s.customer_name, s.email, s.city,
        CURRENT_DATE, NULL, TRUE
    FROM staging_customer s
    INNER JOIN dim_customer d 
        ON s.customer_id = d.customer_id
    WHERE d.expiration_date = CURRENT_DATE;

    -- Step 3: Insert new customers
    INSERT INTO dim_customer 
        (customer_id, customer_name, email, city, 
         effective_date, expiration_date, is_current)
    SELECT 
        s.customer_id, s.customer_name, s.email, s.city,
        CURRENT_DATE, NULL, TRUE
    FROM staging_customer s
    WHERE NOT EXISTS (
        SELECT 1 FROM dim_customer d 
        WHERE d.customer_id = s.customer_id
    );

    COMMIT;
END;
$$;
```

---

## Behavioral/Scenario Questions

### Q13: "Tell me about a time you implemented SCD Type 2"

**STAR Format Answer:**

**Situation:** "At my previous company, we needed to track customer address changes for shipping cost analysis and compliance."

**Task:** "I was responsible for redesigning the customer dimension table to preserve historical addresses."

**Action:** 
- "I implemented SCD Type 2 with surrogate keys and temporal columns"
- "Created an ETL process using staging tables and change detection"
- "Added indexes on customer_id and is_current flag for performance"
- "Implemented error handling for NULL values and duplicate detection"

**Result:** 
- "Successfully tracked 2 years of address history for 500K customers"
- "Enabled accurate historical shipping cost reporting"
- "Reduced query time by 40% using partial indexes"
- "Met audit compliance requirements"

---

### Q14: "How would you handle late-arriving data in SCD Type 2?"

**Answer:**

**Problem:** Data arrives out of order (e.g., receive June data after July data already loaded)

**Solution:**
```sql
-- Instead of using CURRENT_DATE, use the actual transaction date
INSERT INTO dim_customer 
    (customer_id, email, effective_date, expiration_date, is_current)
VALUES 
    ('C001', 'june@email.com', '2024-06-15', '2024-07-01', FALSE);

-- Update the previously current record
UPDATE dim_customer 
SET effective_date = '2024-07-01'
WHERE customer_id = 'C001' 
  AND is_current = TRUE;
```

**Best Practice:**
- Use business date/transaction date, not load date
- Implement data quality checks to detect late arrivals
- Consider using effective_timestamp instead of effective_date for precision

---

## Quick Cheat Sheet for Interview

### Must Remember:
1. **SCD Type 2 = History preservation by adding rows**
2. **Surrogate key in FK, not natural key**
3. **Three key fields: effective_date, expiration_date, is_current**
4. **NULL expiration_date = current record**
5. **Process: Detect → Close old → Insert new**

### SQL Pattern to Memorize:
```sql
-- Close old
UPDATE dimension SET expiration_date = CURRENT_DATE, is_current = FALSE
WHERE natural_key = X AND is_current = TRUE;

-- Insert new
INSERT INTO dimension VALUES (new_values, CURRENT_DATE, NULL, TRUE);
```

### Common Mistakes to Mention You'd Avoid:
1. Using natural key as FK (wrong - use surrogate)
2. Forgetting to set is_current = FALSE
3. Not handling NULL values in comparisons
4. Missing indexes on is_current flag
5. Using expiration_date check without is_current flag

---

## Practice Question

**"Design a solution to track employee salary changes over time using SCD Type 2"**

**Quick Answer Framework:**
1. Table structure with surrogate key
2. Natural key = employee_id
3. Track: salary, department, effective_date, expiration_date, is_current
4. ETL process for detecting changes
5. Indexing strategy
6. Sample queries for current salary vs historical
