# FAANG Data Engineering Interview Questions

Advanced interview questions commonly asked at Meta, Amazon, Apple, Netflix, Google, and other top tech companies. Focus on distributed systems, scalability, production systems, and system design.

---

## **System Design & Architecture**

### **Question 1: Design a Real-Time Analytics Dashboard**

Design a system that processes 10 million events per second from a mobile app and displays real-time metrics on a dashboard with <1 second latency.

**Requirements:**
- Events include: user actions, page views, errors, performance metrics
- Dashboard shows: DAU/MAU, active users right now, top features, error rates
- Historical data retention: 90 days detailed, 2 years aggregated
- Global user base across multiple regions

**Tasks:**

a) Design the end-to-end architecture (ingestion → processing → storage → serving)  
b) Choose technologies for each component and justify your choices  
c) How do you handle late-arriving data?  
d) How do you ensure exactly-once processing semantics?  
e) Design the data model for both real-time and historical queries  
f) How would you handle a sudden 10x traffic spike?  
g) Estimate the infrastructure cost for this system

**Follow-up:** How would you modify this design if the requirement changed to 100 million events/second?

**Topics Covered:** Stream processing, Lambda/Kappa architecture, distributed systems, data modeling, cost optimization

---

### **Question 2: Build a Recommendation Engine Data Pipeline**

You're building the data pipeline for a product recommendation system like Amazon's "Customers who bought this also bought..."

**Requirements:**
- 500 million users, 100 million products
- User interaction events: views, clicks, purchases, ratings
- Models retrained daily with fresh data
- Recommendations served with <100ms p99 latency
- Support A/B testing of different recommendation algorithms

**Tasks:**

a) Design the ETL pipeline from raw events to model-ready features  
b) How do you handle the cold-start problem for new users/products?  
c) Design the feature store architecture  
d) How do you version your features and models?  
e) Describe your strategy for A/B testing and metric computation  
f) How do you handle PII and data privacy requirements?  
g) Design the serving infrastructure for real-time recommendations

**Topics Covered:** Feature engineering, ML pipelines, feature stores, A/B testing, data privacy, low-latency serving

---

### **Question 3: Design a Data Lake for Multi-Tenant SaaS**

Design a data lake for a B2B SaaS company with 10,000 customer organizations, where each customer can run analytics on their own data.

**Requirements:**
- Customers range from 100GB to 50TB of data
- Support SQL queries, BI tools, and ML workloads
- Strong data isolation between customers
- Cost attribution per customer
- Support both batch and streaming ingestion
- Meet SOC2 and GDPR compliance

**Tasks:**

a) Design the storage layer and partitioning strategy  
b) How do you enforce data isolation and access control?  
c) Design the compute layer for query processing  
d) How do you handle cost attribution and charge-back?  
e) Describe your approach to schema evolution  
f) How do you optimize for customers with very different data sizes?  
g) Design the metadata and catalog layer

**Topics Covered:** Multi-tenancy, data lake architecture, security, compliance, cost optimization, metadata management

---

## **Performance & Optimization**

### **Question 4: Debug a Slow Spark Job**

You have a Spark job that processes daily transaction data. Yesterday it completed in 2 hours, but today it's been running for 8 hours and still not done. The input data size increased by only 10%.

**Given Information:**
- Job does complex joins and aggregations
- Spark UI shows one stage stuck at 99% complete
- That stage has 2000 tasks, with 1950 complete
- The remaining 50 tasks are all processing partition 1523
- Executor logs show frequent GC warnings on 3 out of 50 executors

**Tasks:**

a) Diagnose the root cause(s) of the performance degradation  
b) Explain why a 10% data increase caused a 4x slowdown  
c) Provide specific Spark configurations to fix this  
d) Rewrite the problematic code sections with optimizations  
e) How would you prevent this issue in the future?  
f) Design a monitoring system to catch similar issues early

**Topics Covered:** Debugging, data skew, Spark internals, performance tuning, monitoring

---

### **Question 5: Optimize a Daily Batch Job**

You have a daily batch job that processes clickstream data:
- Input: 5TB of JSON files in S3
- Processing: Parse JSON, join with dimension tables, aggregate metrics
- Output: Write to data warehouse (Redshift/Snowflake)
- Current runtime: 6 hours
- SLA: Must complete in 4 hours

**Current Implementation:**
```python
# Pseudocode
df = spark.read.json("s3://bucket/clickstream/*/*")
df = df.join(user_dim, "user_id")
df = df.join(product_dim, "product_id")
df = df.join(geo_dim, "ip_address")
df = df.groupBy("date", "country", "product_category").agg(...)
df.write.format("parquet").save("s3://output/")
```

**Tasks:**

a) Identify at least 5 performance bottlenecks  
b) Rewrite the code with optimizations  
c) Recommend infrastructure changes (instance types, cluster size, etc.)  
d) Design a file format and partitioning strategy for the input data  
e) How would you make this job incremental instead of full refresh?  
f) Estimate the cost savings from your optimizations

**Topics Covered:** Batch optimization, broadcast joins, partitioning, file formats, incremental processing

---

### **Question 6: Scale a Database Migration**

You need to migrate 100TB of data from Oracle to Snowflake with minimal downtime.

**Constraints:**
- Production system can't have more than 1 hour of downtime
- Data is constantly being updated
- Must maintain referential integrity
- Zero data loss tolerance
- Some tables have 10+ billion rows

**Tasks:**

a) Design the migration strategy and timeline  
b) How do you handle the delta/CDC during migration?  
c) Design the validation process to ensure data integrity  
d) How do you handle the cutover with minimal downtime?  
e) What's your rollback plan if something goes wrong?  
f) Estimate the time and cost for this migration

**Topics Covered:** Database migration, CDC, zero-downtime deployments, validation strategies

---

## **Data Quality & Reliability**

### **Question 7: Build a Data Quality Framework**

Design a comprehensive data quality framework for a company with 500+ data pipelines feeding 100+ business-critical dashboards.

**Common Issues:**
- Schema changes breaking downstream pipelines
- Duplicate records
- Missing data for certain time periods
- Data arriving with incorrect values
- Stale data not being updated

**Tasks:**

a) Design a data quality taxonomy (what to check at each stage)  
b) Implement automated data quality checks in code  
c) Design the alerting and incident response workflow  
d) How do you handle data quality SLAs?  
e) Create a data lineage tracking system  
f) Design a self-healing mechanism for common failure patterns  
g) How do you measure and report on data quality metrics?

**Topics Covered:** Data quality, observability, SLAs, data lineage, incident management

---

### **Question 8: Handle a Production Data Incident**

At 9 AM on Monday, your monitoring alerts that yesterday's revenue metrics are off by 30%. The CEO is asking questions.

**What you know:**
- The ETL job ran successfully (no errors)
- Data volume looks normal
- One upstream API changed response format on Sunday
- Some revenue records have NULL values where they shouldn't

**Tasks:**

a) Walk through your immediate response (first 30 minutes)  
b) How do you assess the blast radius and impact?  
c) Design a fix and backfill strategy  
d) How do you prevent similar issues in the future?  
e) Write a post-mortem document outline  
f) What process changes would you implement?

**Topics Covered:** Incident response, root cause analysis, backfilling, post-mortems, prevention

---

## **SQL & Query Optimization**

### **Question 9: Complex SQL Query**

Given these tables in a social media platform:

```sql
users (user_id, username, created_at, country)
posts (post_id, user_id, content, created_at, likes_count)
follows (follower_id, following_id, created_at)
comments (comment_id, post_id, user_id, content, created_at)
```

**Write queries for:**

a) Find the top 10 users by engagement rate in the last 30 days, where engagement rate = (likes + comments received) / followers. Handle users with 0 followers.

b) For each user, find their "influence score": their follower count + (sum of their followers' follower counts * 0.1). Return top 100 influencers.

c) Detect potential bot accounts: users who posted >50 times/day for 7+ consecutive days in the last month.

d) Find "viral posts": posts that got >1000 likes within 24 hours of posting AND had >50% of likes from users who don't follow the author.

e) Calculate a "retention cohort analysis": for users who joined in each month, what % were still active (posted/commented) 1 month, 3 months, and 6 months later?

**Follow-ups:**
- Optimize each query for a table with 1 billion posts
- Which queries should be pre-computed/materialized?
- How would you partition these tables in Spark/Hive?

**Topics Covered:** Complex SQL, window functions, CTEs, query optimization, materialized views

---

### **Question 10: Window Functions Master Class**

Given a `sales` table:
```sql
sales (sale_id, product_id, customer_id, amount, sale_date, region)
```

**Write queries for:**

a) Running total of sales by product, ordered by date

b) Month-over-month growth rate by region

c) For each sale, show the difference from the region's median sale amount that month

d) Find customers whose last 3 purchases were all increasing in value

e) Identify products with declining sales (negative trend over last 6 months using linear regression)

f) For each product, find "whale customers" (those whose total purchases are in the top 10% for that product)

g) Detect "seasonality": products whose sales variance by month is >50% of annual average

**Advanced:**
- Rewrite these using QUALIFY clause (if available)
- Optimize for a 10TB table partitioned by date
- Which window function operations can benefit from CLUSTER BY?

**Topics Covered:** Window functions, statistical analysis in SQL, advanced analytics, performance optimization

---

## **Distributed Systems Concepts**

### **Question 11: CAP Theorem in Practice**

You're designing a global multi-region data system for financial transactions.

**Scenarios:**

a) **Payment Processing:** Users can make payments from any region. How do you ensure:
   - No double-spending
   - Transaction history is consistent globally
   - System remains available during network partitions
   
   Which of CAP do you sacrifice and why?

b) **Analytics Dashboard:** Real-time metrics across all regions. How do you design for:
   - Low query latency
   - High availability
   - Eventual consistency acceptable
   
   Explain your replication strategy.

c) **Fraud Detection:** Must process transactions in real-time and block suspicious ones. How do you balance:
   - Consistency (blocking fraudulent transactions)
   - Availability (not blocking legitimate users)
   - Partition tolerance
   
   Design your system and explain tradeoffs.

**Topics Covered:** CAP theorem, distributed systems, consistency models, replication

---

### **Question 12: Design a Distributed Task Scheduler**

Design a system like Airflow/Temporal that can schedule and execute millions of tasks per day.

**Requirements:**
- Support DAG-based task dependencies
- Handle task retries and failure recovery
- Support both scheduled and event-driven workflows
- Provide observability (logs, metrics, traces)
- Multi-tenant with resource isolation
- Scale to 100,000+ concurrent tasks

**Tasks:**

a) Design the architecture (coordinator, workers, metadata store)  
b) How do you ensure exactly-once task execution?  
c) Design the scheduling algorithm  
d) How do you handle worker failures mid-task?  
e) Design the metadata store schema  
f) How do you handle backpressure when tasks are queued faster than execution?  
g) Implement priority queues and resource quotas

**Topics Covered:** Distributed systems, scheduling algorithms, fault tolerance, scalability

---

## **Spark Deep Dive**

### **Question 13: Explain Spark Internals**

**Scenario:** You run this code:
```scala
val df1 = spark.read.parquet("s3://bucket/large_table")  // 1TB, 10,000 files
val df2 = spark.read.parquet("s3://bucket/small_table")  // 1GB, 10 files

val joined = df1.join(df2, "key")
  .groupBy("category")
  .agg(sum("amount"))
  .orderBy(desc("sum(amount)"))
  
joined.write.parquet("s3://output/")
```

**Questions:**

a) Draw the DAG of stages and explain stage boundaries  
b) How many shuffles occur? Why?  
c) Explain the physical execution plan  
d) How does Spark decide partition counts at each stage?  
e) What optimizations does Catalyst apply?  
f) Explain Tungsten optimizations that apply here  
g) How would you optimize this code?  
h) Explain the difference between narrow and wide transformations in this context

**Topics Covered:** Spark internals, Catalyst optimizer, Tungsten, DAG execution, performance tuning

---

### **Question 14: Custom Spark Optimization**

You have a use case that Spark doesn't optimize well:

**Problem:** 
- Large fact table (10TB) with highly skewed user_id
- Need to join with a medium dimension table (100GB)
- 90% of data is for 10% of user_ids (power users)
- Standard broadcast join fails (dimension too large)
- Standard shuffle join has severe skew

**Tasks:**

a) Implement a custom partitioner that handles this skew  
b) Write a hybrid join strategy (broadcast for common keys, shuffle for others)  
c) Implement custom aggregation logic using mapPartitions  
d) Create a custom data source that pushes down predicates  
e) Write a Catalyst optimization rule for your use case  
f) Benchmark your solution vs standard Spark

**Topics Covered:** Advanced Spark, custom partitioners, Catalyst rules, performance engineering

---

## **Streaming & Real-Time**

### **Question 15: Design a Real-Time ML Feature Store**

Design a feature store that serves features for real-time ML predictions with <10ms p99 latency.

**Requirements:**
- 10,000 features across 100 feature groups
- Mix of batch features (updated daily) and streaming features (real-time)
- Support point-in-time correct joins for training
- Handle 1M+ QPS for online serving
- Maintain consistency between training and serving

**Tasks:**

a) Design the storage layer (batch vs streaming features)  
b) Design the serving layer for low-latency access  
c) How do you handle feature versioning and backfilling?  
d) Implement point-in-time correct joins for training data  
e) Design the feature computation pipeline (batch + streaming)  
f) How do you monitor feature drift?  
g) Design the feature catalog and discovery system

**Topics Covered:** Feature stores, ML systems, streaming processing, low-latency serving

---

### **Question 16: Build Exactly-Once Kafka Processing**

Implement exactly-once semantics for a Kafka Streams application that:
- Reads from topic A (user events)
- Enriches with data from topic B (user profiles)
- Aggregates metrics per user
- Writes to topic C (processed events) and database (aggregations)

**Challenges:**
- Network failures during processing
- Duplicate messages in source topic
- Database writes must be idempotent
- Consumer rebalancing during processing

**Tasks:**

a) Explain Kafka's exactly-once semantics (EOS)  
b) Implement idempotent processing logic  
c) Handle the "dual write" problem (Kafka + DB)  
d) Design the state store for aggregations  
e) Implement proper error handling and retries  
f) How do you test exactly-once guarantees?  
g) What are the performance tradeoffs of EOS?

**Topics Covered:** Kafka, exactly-once semantics, stream processing, idempotency, distributed transactions

---

## **Cloud & Infrastructure**

### **Question 17: Multi-Cloud Data Strategy**

Your company uses AWS for primary workloads but needs to support Azure and GCP for regulatory reasons (data residency in certain countries).

**Requirements:**
- Data must stay in specific regions
- Need unified analytics across all clouds
- Minimize data transfer costs
- Support disaster recovery
- Unified governance and access control

**Tasks:**

a) Design the multi-cloud architecture  
b) Choose data replication strategy  
c) Design the query federation layer  
d) Handle cost optimization across clouds  
e) Implement unified security and governance  
f) Design the disaster recovery strategy  
g) Estimate the cost premium of multi-cloud vs single cloud

**Topics Covered:** Multi-cloud architecture, data replication, federation, cost optimization

---

### **Question 18: Cost Optimization Challenge**

Your monthly AWS bill for data infrastructure is $500K and growing. Breakdown:
- EMR/Dataproc: $200K
- S3: $100K
- Redshift/Snowflake: $150K
- Data Transfer: $50K

**Tasks:**

a) Identify cost optimization opportunities in each category  
b) Design a chargeback system to allocate costs to teams  
c) Implement automated cost anomaly detection  
d) Optimize storage (lifecycle policies, compression, formats)  
e) Optimize compute (spot instances, autoscaling, right-sizing)  
f) Design a cost governance framework  
g) Estimate potential savings (target: 30% reduction)

**Topics Covered:** Cost optimization, FinOps, resource management, governance

---

## **Coding Challenges**

### **Question 19: Implement a Data Deduplication Algorithm**

Given a dataset with potential duplicates where records might have:
- Exact duplicates (all fields match)
- Near duplicates (slight variations in names, addresses)
- Fuzzy matches (typos, abbreviations)

**Example:**
Record 1: {name: "John Smith", email: "john@email.com", phone: "555-1234"}
Record 2: {name: "Jon Smith", email: "john@email.com", phone: "555-1234"}
Record 3: {name: "John Smith", email: "jsmith@email.com", phone: "555-1234"}

**Tasks:**

a) Design a similarity algorithm (how to score matches)  
b) Implement in PySpark for 1 billion records  
c) Handle the N² comparison problem efficiently  
d) Make it work in a streaming context (incremental dedup)  
e) Allow user-defined matching rules  
f) Optimize for both precision and recall  
g) Benchmark performance and tune

**Topics Covered:** Algorithm design, fuzzy matching, distributed computing, optimization

---

### **Question 20: Build a Time-Series Compression Algorithm**

You have 1PB of time-series sensor data with high redundancy. Design a compression system.

**Data characteristics:**
- Values change slowly (mostly consecutive duplicates)
- Precision: 2 decimal places sufficient
- Timestamps are regular (1 second intervals)
- Need to support range queries efficiently

**Tasks:**

a) Design the compression algorithm  
b) Implement delta encoding for timestamps  
c) Implement run-length encoding for values  
d) Support efficient range queries without full decompression  
e) Compare your approach vs Parquet/ORC  
f) Estimate compression ratio  
g) Implement in Spark for distributed compression  
h) Benchmark query performance

**Topics Covered:** Compression algorithms, encoding techniques, columnar formats, performance optimization

---

## **Answer Expectations**

### **What Interviewers Look For:**

**System Design Questions:**
- Structured thinking and problem decomposition
- Justification for technology choices
- Understanding of tradeoffs
- Scalability and performance considerations
- Cost awareness
- Real-world production experience

**Coding Questions:**
- Working code (not just pseudocode)
- Edge case handling
- Performance optimization
- Testing strategy
- Code quality and maintainability

**Troubleshooting Questions:**
- Systematic debugging approach
- Deep technical knowledge
- Tool proficiency (Spark UI, logs, metrics)
- Root cause analysis
- Prevention mindset

---

## **Preparation Tips**

**For System Design:**
- Practice drawing architectures on whiteboard
- Study real-world systems (Netflix, Uber, Meta blogs)
- Understand fundamental distributed systems concepts
- Know the pros/cons of major technologies
- Practice cost estimation

**For Coding:**
- Master Spark/SQL in your language of choice
- Practice on large datasets (not toy examples)
- Learn to optimize beyond "make it work"
- Understand algorithmic complexity
- Practice live coding with interviewer questions

**For Troubleshooting:**
- Get hands-on with production systems
- Practice reading Spark UI, logs, metrics
- Learn common failure patterns
- Study post-mortems from major incidents
- Understand performance profiling tools

---

## **Common Follow-Up Questions**

- "How would this design change at 10x/100x scale?"
- "What would you do differently with unlimited budget vs limited budget?"
- "How do you handle this in a multi-region deployment?"
- "What monitoring would you add?"
- "How do you test this?"
- "What's your disaster recovery plan?"
- "How do you handle schema evolution?"
- "What are the security implications?"

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-01  
**Target Audience:** Senior Data Engineers, Staff+ Engineers interviewing at FAANG  
**Difficulty:** Advanced
