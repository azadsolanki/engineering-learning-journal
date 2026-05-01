# SQL & Spark Interview Questions

A comprehensive collection of interview questions covering SQL, Spark, and DBT concepts across fundamental, medium, and hard difficulty levels.

---

## **Fundamental Level**

### **Question 1: SQL Basics - NULL Handling**

You have a table `employees` with columns: `id`, `name`, `department`, `salary`. Some salary values are NULL.

Write a query to find all employees whose salary is NULL. Would `WHERE salary = NULL` work? If not, why and what's the correct syntax?

**Topics Covered:** NULL handling, SQL fundamentals, common pitfalls

---

### **Question 2: Basic Join Understanding**

Given two tables:
- `students`: id, name (5 rows with IDs 1, 2, 3, 4, 5)
- `grades`: student_id, grade (3 rows for student_ids 1, 2, 3)

How many rows will each of these queries return?

```sql
a) SELECT * FROM students INNER JOIN grades ON students.id = grades.student_id
b) SELECT * FROM students LEFT JOIN grades ON students.id = grades.student_id
c) SELECT * FROM students CROSS JOIN grades
```

**Topics Covered:** JOIN types, cardinality, result set size calculation

---

### **Question 3: Spark Job Basics**

Explain the role of the Driver and Executors in a Spark application. What happens if the Driver fails during job execution?

**Topics Covered:** Spark architecture, Driver/Executor roles, fault tolerance

---

## **Medium Level**

### **Question 4: Set Operations - UNION vs UNION ALL**

You have two tables with duplicate values:
- Table A: [10, 10, 20, 30]
- Table B: [10, 20, 20, 40, 50]

Write queries for both UNION and UNION ALL, and explain:

a) How many rows each will return  
b) Which one is faster and why  
c) A real-world scenario where you'd prefer UNION ALL over UNION

**Topics Covered:** Set operations, performance implications, deduplication

---

### **Question 5: DBT Macros**

You need to create a reusable DBT macro that:
- Takes a date column and a date format as parameters
- Returns SQL that converts the date to the specified format
- Has a default format of 'YYYY-MM-DD'

Write the macro and show how you'd use it in a model. What are the benefits of using macros versus copying the same SQL logic across multiple models?

**Topics Covered:** DBT macros, Jinja templating, code reusability, DRY principles

---

### **Question 6: Spark Memory Management**

Your Spark job processes a 500GB dataset with the following config:
- 10 executors
- 4GB executor memory each
- spark.sql.shuffle.partitions = 200

The job fails during a `groupBy` operation with "OutOfMemoryError: Java heap space" on executors. Identify three possible causes and propose solutions for each.

**Topics Covered:** Memory management, OOM errors, Spark configuration tuning, troubleshooting

---

## **Hard Level**

### **Question 7: Data Skew & Optimization**

You have a Spark job that joins two tables:
- `transactions` (1 billion rows) with columns: user_id, amount, date
- `users` (10 million rows) with columns: user_id, name, segment

10% of transactions belong to user_id = 'GUEST'. The join is causing severe data skew with one executor running 10x longer than others.

**Tasks:**

a) Explain why this skew occurs  
b) Propose at least two different optimization strategies (with code examples)  
c) How would you use DISTRIBUTE BY or CLUSTER BY to optimize a subsequent aggregation on this joined data?

**Topics Covered:** Data skew, join optimization, salting techniques, DISTRIBUTE BY, CLUSTER BY

---

### **Question 8: Custom DBT Materialization**

You need to implement a custom DBT materialization called "snapshot_scd2" that:
- Implements Type 2 Slowly Changing Dimensions
- Tracks historical changes with `effective_start_date` and `effective_end_date`
- Marks current records with `is_current = true`
- On first run, creates the table with all records as current
- On subsequent runs, expires old records and inserts new versions

**Tasks:**

a) Write the skeleton structure of this custom materialization  
b) Explain when you'd use this versus DBT's built-in snapshot functionality  
c) What are the tradeoffs of creating custom materializations?

**Topics Covered:** Custom materializations, SCD Type 2, DBT internals, dimensional modeling

---

### **Question 9: Complex Query Optimization**

Given this query that's running slowly on a 10TB table:

```sql
SELECT 
    customer_id,
    product_category,
    COUNT(*) as purchase_count,
    SUM(amount) as total_spent,
    AVG(amount) as avg_spent
FROM transactions
WHERE transaction_date >= '2024-01-01'
    AND amount > 0
    AND status IN ('completed', 'pending')
GROUP BY customer_id, product_category
HAVING COUNT(*) > 5
DISTRIBUTE BY customer_id
CLUSTER BY product_category
ORDER BY total_spent DESC
LIMIT 1000
```

The table is partitioned by `transaction_date` but has severe data skew on `customer_id` (top 1% of customers generate 40% of transactions).

**Tasks:**

a) Identify at least 3 performance issues with this query  
b) Explain the execution plan: what happens with DISTRIBUTE BY, CLUSTER BY, and ORDER BY together?  
c) Rewrite the query with optimizations including proper partitioning strategy, skew handling, and correct use of sorting/distribution clauses  
d) Would pushing down the LIMIT help? Why or why not?

**Topics Covered:** Query optimization, execution plans, partition pruning, skew handling, clause ordering

---

## **Bonus Challenge Question**

### **Question 10: End-to-End Architecture Design**

Design a data pipeline that:
- Ingests daily transaction data (100GB/day) from multiple sources
- Transforms it through bronze → silver → gold layers
- Handles late-arriving data (up to 7 days late)
- Supports both batch and streaming workloads
- Implements data quality checks at each layer

**Using Spark and DBT, address the following:**

a) Describe the architecture and technology choices for each layer  
b) How would you handle incremental processing in both Spark and DBT?  
c) Where would you use custom DBT materializations and why?  
d) How would you handle the scenario where a source system sends duplicate records?  
e) Design the monitoring and alerting strategy for data quality issues

**Topics Covered:** Data architecture, medallion architecture, incremental processing, data quality, streaming vs batch, monitoring, end-to-end pipeline design

---

## **Answer Key Guide**

### Expected Answer Components

**Fundamental Questions:**
- Clear, concise explanations
- Correct syntax and understanding of basics
- Awareness of common pitfalls

**Medium Questions:**
- Deeper technical understanding
- Performance considerations
- Real-world application scenarios
- Code examples

**Hard Questions:**
- Advanced optimization techniques
- Multiple solution approaches
- Tradeoff analysis
- Architectural thinking
- Production-grade considerations

---

## **Interview Tips**

**For Interviewers:**
- Start with fundamental questions to assess baseline knowledge
- Use medium questions to evaluate practical experience
- Reserve hard questions for senior roles or deep dives
- Allow candidates to ask clarifying questions
- Look for thought process, not just correct answers

**For Candidates:**
- Think aloud to show your reasoning
- Ask clarifying questions about data volumes, SLAs, etc.
- Discuss tradeoffs between different approaches
- Relate answers to real-world scenarios you've encountered
- Don't be afraid to say "I don't know, but here's how I'd find out"

---

## **Related Topics to Explore**

- Window functions in SQL
- Spark catalyst optimizer
- DBT testing strategies
- Data warehouse design patterns
- Cost optimization in cloud data platforms
- Real-time vs batch processing tradeoffs
- Data quality frameworks
- Metadata management

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-30  
**Topics Covered:** SQL, Spark, DBT, Data Engineering, Performance Optimization
