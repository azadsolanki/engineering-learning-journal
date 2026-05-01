# Snowflake Interview Answers - Concise Edition
## Short, Direct Answers for Data Engineer Interviews

---

## **ARCHITECTURE & BASICS**

### Q: Explain Snowflake's architecture in 3 sentences.

**Answer:**
"Snowflake has three layers: storage, compute, and cloud services. Storage layer holds compressed, columnar data in cloud object storage (S3/Azure/GCS). Compute layer has virtual warehouses that independently access shared storage, allowing multiple teams to query simultaneously without contention."

---

### Q: What are virtual warehouses?

**Answer:**
"Virtual warehouses are clusters of compute resources that execute queries. They're completely separate from storage, can be sized from X-Small to 6X-Large, and you only pay when they're running. Key feature: auto-suspend/auto-resume saves costs by shutting down when idle."

---

### Q: What is micro-partitioning?

**Answer:**
"Snowflake automatically divides tables into 50-500MB compressed files called micro-partitions. Each stores metadata (min/max values, null counts) enabling partition pruning - Snowflake skips irrelevant partitions without scanning data. No manual partitioning needed."

---

### Q: Explain Time Travel.

**Answer:**
"Time Travel lets you query data as it existed in the past (up to 90 days). Use it to recover dropped tables, query historical data, or undo changes. Syntax: `SELECT * FROM table AT(OFFSET => -3600)` for 1 hour ago."

---

### Q: What's the difference between Time Travel and Fail-safe?

**Answer:**
"Time Travel: User-accessible, 0-90 days retention, can query/restore data. Fail-safe: Snowflake-only disaster recovery, 7 days after Time Travel expires, only Snowflake support can recover. Time Travel = your control, Fail-safe = Snowflake's safety net."

---

## **TABLE TYPES**

### Q: What are the different table types in Snowflake?

**Answer:**
"Snowflake has 4 main table types:

1. **Permanent** - Default, full Time Travel (0-90 days), 7-day Fail-safe, standard storage costs
2. **Transient** - Time Travel (0-1 day), NO Fail-safe, ~30% cheaper storage
3. **Temporary** - Session-only, 1-day Time Travel, no Fail-safe, auto-drops when session ends
4. **External** - Data stays in S3/Azure/GCS, metadata only in Snowflake, no Time Travel/Fail-safe

Plus **Clone** tables (zero-copy of existing tables) and **Hybrid** tables (row-based with unique key enforcement)."

---

### Q: When would you use each table type?

**Answer:**
"**Permanent:** Production fact/dimension tables, anything needing recovery or audit (e.g., `fact_sales`, `dim_customer`)

**Transient:** ETL staging, intermediate transformations you can recreate (e.g., `staging_orders`, `temp_aggregates`)

**Temporary:** Session-specific work, testing, ad-hoc analysis (e.g., complex query breakdowns)

**External:** Query files without ingesting - logs, archives, data lake exploration (e.g., raw S3 parquet files)

**Rule of thumb:** If you can't afford to lose it → Permanent. If you can rebuild it → Transient. If it's just for this session → Temporary."

---

### Q: Compare storage costs across table types.

**Answer:**
"Assume 100GB table:

| Type | Time Travel | Fail-safe | Total Storage | Relative Cost |
|------|-------------|-----------|---------------|---------------|
| Permanent (1 day TT) | 100GB | 100GB | 200GB | 100% |
| Permanent (7 day TT) | 700GB | 100GB | 800GB | 400% |
| Transient (1 day TT) | 100GB | 0GB | 100GB | 50% |
| Temporary | 100GB | 0GB | 100GB | 50% |
| External | Metadata only | 0GB | ~1MB | ~0% |

**Key insight:** Transient saves 50% vs permanent by eliminating Fail-safe. External costs almost nothing in Snowflake storage."

---

### Q: What are temporary tables good for?

**Answer:**
"Temporary tables exist only for your session - invisible to others, auto-drop when you disconnect. Use for: 

1. Breaking complex queries into steps
2. Testing transformations before productionizing
3. Session-specific calculations/aggregates
4. Isolating work without cluttering database

Example: ETL testing - load sample data to temp table, test transformations, iterate without affecting anyone."

---

### Q: What are external tables and their limitations?

**Answer:**
"External tables query S3/Azure/GCS files directly without loading into Snowflake. Metadata stored in Snowflake, data stays external.

**Pros:** No data movement, no storage cost in Snowflake, query immediately
**Cons:** Slower queries (network I/O), no micro-partitioning benefits, no Time Travel, no clustering, can't UPDATE/DELETE

**Use when:** Exploratory analysis of data lake, rarely-queried archives, want to avoid duplication, data owned by another system."

---

### Q: What are Hybrid tables?

**Answer:**
"Hybrid tables (newer feature) are row-based with unique key enforcement - unlike standard Snowflake tables which are append-only columnar. Support UPSERT, enforce primary/foreign keys, optimized for single-row lookups. Use for: operational/transactional data, serving layer for apps, when you need fast key-based lookups. Trade-off: not as fast for analytics scans."

---

### Q: What happens to Time Travel storage when you drop a table?

**Answer:**
"**Permanent tables:** Time Travel data retained for configured period (up to 90 days), then moves to Fail-safe for 7 days, then permanently deleted. You pay storage for dropped table's Time Travel period.

**Transient/Temporary:** Time Travel data retained (up to 1 day), then permanently deleted. No Fail-safe.

**Cost tip:** Use `DROP TABLE ... PURGE` to immediately delete without Time Travel retention if you're certain you don't need recovery."

---

### Q: When would you use transient vs permanent tables?

**Answer:**
"Use transient for staging/temp data you can recreate - they have 1-day Time Travel and no Fail-safe (cheaper). Use permanent for production data needing full recovery - they have up to 90-day Time Travel and 7-day Fail-safe. Cost savings: transient tables reduce storage by ~30% for intermediate ETL stages."

---

## **PERFORMANCE OPTIMIZATION**

### Q: What is clustering and when do you use it?

**Answer:**
"Clustering physically co-locates data by specified columns. Use for: (1) Tables >1TB, (2) Consistent filter patterns, (3) High clustering depth (check with `SYSTEM$CLUSTERING_INFORMATION`). Don't cluster small tables - micro-partitioning is usually sufficient. Limit to 3-4 columns."

---

### Q: How do you optimize a slow query?

**Answer:**
"1. Check Query Profile for bottlenecks (spilling, partition scans). 2. Ensure filters use partition-friendly syntax (no functions on WHERE columns). 3. Check for remote spilling - scale up warehouse if needed. 4. Add clustering if table is large with consistent filters. 5. Use RESULT_SCAN to reuse previous results."

---

### Q: What causes data spilling?

**Answer:**
"Spilling happens when query intermediate results exceed warehouse memory. Local spilling: slower but manageable. Remote spilling: much slower, bad sign. Fixes: (1) Scale up warehouse, (2) Reduce data volume with better filters, (3) Optimize joins, (4) Break complex queries into steps with temp tables."

---

### Q: Explain result caching.

**Answer:**
"Result cache stores query results for 24 hours. If you run the exact same query (same SQL text, same objects), Snowflake returns cached results instantly - no compute cost. Invalidated by: data changes, time-based functions (CURRENT_TIMESTAMP), or cache expiry. Tip: Remove CURRENT_TIMESTAMP from queries to enable caching."

---

### Q: What's the difference between scaling up vs scaling out?

**Answer:**
"Scale up: Increase warehouse size (SMALL → MEDIUM → LARGE) - more memory/CPU per node. Better for complex queries with large joins/aggregations. Scale out: Add clusters (multi-cluster warehouse) - more concurrent query capacity. Better for many users running queries simultaneously. Cost doubles with each scale-up level."

---

## **COST OPTIMIZATION**

### Q: How do you control Snowflake costs?

**Answer:**
"1. Resource monitors: Set credit quotas with alerts/suspend at thresholds. 2. Auto-suspend: Set to 5-10 minutes. 3. Right-size warehouses: Don't over-provision. 4. Cluster queries efficiently: Avoid unnecessary scans. 5. Monitor: Use ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY to find waste. 6. Transient tables for staging. 7. Statement timeout to kill runaway queries."

---

### Q: What's a resource monitor?

**Answer:**
"Resource monitors limit warehouse credit consumption. Set monthly/weekly quotas and define actions at thresholds: notify at 75%, suspend at 90%, immediate suspend at 100%. Apply to specific warehouses or account-wide. Critical for preventing bill shock from runaway queries."

---

### Q: How do you identify expensive queries?

**Answer:**
```sql
SELECT query_text, 
       execution_time/1000 as seconds,
       warehouse_size,
       total_elapsed_time/1000 as total_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY total_elapsed_time DESC
LIMIT 10;
```

---

## **DATA LOADING**

### Q: Explain COPY INTO vs Snowpipe.

**Answer:**
"COPY INTO: Batch loading command, you trigger manually/scheduled, good for large files. Snowpipe: Continuous micro-batch loading, auto-triggers when files land in stage, good for streaming data. Snowpipe uses serverless compute (separate billing). Use Snowpipe for real-time needs, COPY for bulk loads."

---

### Q: How do you load data from S3?

**Answer:**
```sql
-- 1. Create stage
CREATE STAGE my_s3_stage 
  URL='s3://bucket/path/'
  CREDENTIALS=(AWS_KEY_ID='...' AWS_SECRET_KEY='...');

-- 2. Copy data
COPY INTO my_table
FROM @my_s3_stage
FILE_FORMAT = (TYPE=CSV SKIP_HEADER=1)
ON_ERROR = CONTINUE;
```

---

### Q: What are stages?

**Answer:**
"Stages are locations for data files. Three types: (1) User stage: personal, @~, (2) Table stage: per-table, @%table_name, (3) Named stage: shared, @stage_name. Named stages can be internal (Snowflake storage) or external (S3/Azure/GCS). Use for COPY INTO and unloading data."

---

## **SEMI-STRUCTURED DATA**

### Q: How does Snowflake handle JSON?

**Answer:**
"Use VARIANT data type to store JSON/XML/Parquet. Query with colon notation: `json_column:field_name`. Extract with bracket notation for arrays: `json_column[0]:name`. Flatten nested arrays with LATERAL FLATTEN. Snowflake auto-parses JSON and stores efficiently - no pre-processing needed."

---

### Q: Example of querying JSON?

**Answer:**
```sql
CREATE TABLE events (event_data VARIANT);

-- Query nested JSON
SELECT 
  event_data:user_id::STRING as user_id,
  event_data:event_type::STRING as event_type,
  event_data:metadata:browser::STRING as browser
FROM events
WHERE event_data:event_type = 'page_view';
```

---

## **SECURITY & GOVERNANCE**

### Q: Explain Snowflake's RBAC.

**Answer:**
"Role-Based Access Control uses hierarchical roles. Key roles: ACCOUNTADMIN (top), SYSADMIN (manages objects), SECURITYADMIN (manages users/roles). Grant privileges to roles, not users. Users assume roles. Best practice: Create custom roles for teams, grant least privilege, never give users ACCOUNTADMIN directly."

---

### Q: What are secure views?

**Answer:**
"Secure views hide definition and optimization details, preventing users from inferring underlying data through query plans. Use for: (1) Sensitive data with row-level security, (2) PHI/PII protection, (3) When exposing views to external parties. Downside: some query optimizations disabled."

---

### Q: How do you implement row-level security?

**Answer:**
"Use secure views with CURRENT_ROLE() or CURRENT_USER() in WHERE clause:
```sql
CREATE SECURE VIEW sales_by_region AS
SELECT * FROM sales
WHERE region = (
  SELECT region FROM user_regions 
  WHERE user = CURRENT_USER()
);
```
Users only see their authorized rows."

---

## **CLONING & ZERO-COPY**

### Q: What is zero-copy cloning?

**Answer:**
"CLONE creates instant copy of database/schema/table without copying data. Uses metadata pointers to shared micro-partitions. Near-instant, no storage cost until data diverges. Use for: dev/test environments, backups, experimentation. Example: `CREATE TABLE test_table CLONE prod_table;`"

---

### Q: When does a clone consume storage?

**Answer:**
"Clone only uses storage when data diverges from original. If you INSERT/UPDATE/DELETE in clone, those new/changed micro-partitions consume space. If original table drops old micro-partitions outside Time Travel, clone must retain them (storage cost). Unchanged data = shared = zero cost."

---

## **STREAMS & TASKS**

### Q: What are Streams?

**Answer:**
"Streams track DML changes (INSERT/UPDATE/DELETE) on tables. Acts as CDC (Change Data Capture). Query stream to see changed rows with metadata (METADATA$ACTION, METADATA$ISUPDATE). Use for: incremental processing, real-time pipelines, triggering downstream updates. Stream advances offset when consumed."

---

### Q: What are Tasks?

**Answer:**
"Tasks are scheduled SQL execution. Cron-like scheduling or triggered by Streams. Create dependencies (task DAGs). Use for: scheduled ETL, automatic refresh, data pipeline orchestration. Example: `CREATE TASK refresh_daily SCHEDULE='USING CRON 0 2 * * * UTC' AS ...`"

---

### Q: How do Streams and Tasks work together?

**Answer:**
"Stream tracks changes → Task runs when stream has data → Task processes changes → Stream offset advances. Pattern:
```sql
CREATE STREAM my_stream ON TABLE source;
CREATE TASK process_changes
  WHEN SYSTEM$STREAM_HAS_DATA('my_stream')
AS 
  INSERT INTO target SELECT * FROM my_stream;
```
Enables event-driven pipelines."

---

## **WAREHOUSING & COMPUTE**

### Q: Can multiple warehouses query the same table simultaneously?

**Answer:**
"Yes - that's Snowflake's key advantage. Storage is shared, compute is independent. 10 warehouses can query same table with zero contention. Each has own compute resources. Enables: dev/test isolation, department-specific warehouses, concurrent workloads without interference."

---

### Q: What's a multi-cluster warehouse?

**Answer:**
"Warehouse that auto-scales clusters (horizontal scaling) based on query queue. Set min/max cluster count. As concurrent queries increase, Snowflake adds clusters. As load decreases, removes clusters. Use for: high concurrency, BI tools with many users. Cost: pay per cluster per second running."

---

### Q: What's query queuing?

**Answer:**
"When warehouse at capacity (all slots busy), new queries queue. Slots = 10 × cluster count × warehouse size factor. If queuing occurs regularly, either scale up (more compute per query) or scale out (more concurrent capacity). Check QUERY_HISTORY.queued_overload_time to identify."

---

## **BEST PRACTICES**

### Q: What's your Snowflake cost optimization checklist?

**Answer:**
"1. Auto-suspend ≤ 10 minutes on all warehouses. 2. Resource monitors with 90% suspend trigger. 3. Right-size warehouses - start small. 4. Use transient for staging. 5. Cluster large, frequently-filtered tables. 6. Remove CURRENT_TIMESTAMP from dashboards for caching. 7. Monitor ACCOUNT_USAGE weekly. 8. Kill queries with statement_timeout. 9. Use RESULT_SCAN for dependent queries. 10. Educate users on cost-efficient SQL."

---

### Q: How do you design Snowflake schemas?

**Answer:**
"Use star schemas - Snowflake handles denormalization well. Don't normalize dimensions (no snowflake schema despite the name!). Separate large dimensions with SCD Type 2 using clustering on effective_date. Use transient for staging/ETL intermediates. Partition fact tables only if >1TB and date-filtered queries. Leverage VARIANT for flexible semi-structured data."

---

## **MONITORING & TROUBLESHOOTING**

### Q: Key ACCOUNT_USAGE views?

**Answer:**
"1. WAREHOUSE_METERING_HISTORY: credit consumption. 2. QUERY_HISTORY: all queries, performance metrics. 3. TABLE_STORAGE_METRICS: storage by table. 4. LOAD_HISTORY: data loading stats. 5. AUTOMATIC_CLUSTERING_HISTORY: clustering costs. 6. PIPE_USAGE_HISTORY: Snowpipe monitoring. Latency: 45-min to 3-hour delay."

---

### Q: Query ran yesterday in 10 seconds, today takes 5 minutes. Why?

**Answer:**
"Check: 1. Warehouse suspended? (warm-up time). 2. Data growth in underlying tables? 3. Clustering degraded? (check clustering_depth). 4. Result cache miss? (query changed slightly). 5. Different warehouse size? 6. Concurrent queries causing queue? 7. Statistics stale? (automatic, but can lag). Use Query Profile to compare executions."

---

### Q: How do you handle large dimension tables (50M+ rows)?

**Answer:**
"1. Use clustering on frequently-filtered columns. 2. Consider mini-dimensions for rapidly-changing attributes. 3. Separate current snapshot into materialized view. 4. Partition by effective_date if SCD Type 2. 5. Use appropriate warehouse size. 6. Cache dimension in BI layer if mostly static. In practice: 50M row dimension performs fine with clustering on Snowflake."

---

## **SHARES & DATA EXCHANGE**

### Q: What is Snowflake Data Sharing?

**Answer:**
"Share live data with other Snowflake accounts without copying. Provider creates share, grants access to objects, consumer accesses instantly. No ETL, no data movement - consumers query provider's micro-partitions directly. Use for: vendor data products, partner data exchange, multi-tenant SaaS. Secure and governed."

---

### Q: What's the Data Marketplace?

**Answer:**
"Marketplace to discover and access third-party data. Free and paid datasets. Providers publish data products, consumers subscribe and query instantly in their account. Examples: weather data, financial data, demographics. Use for: enriching internal data, research, quick POCs."

---

## **PRACTICAL SCENARIOS**

### Q: Bill jumped 300% - how do you investigate?

**Answer:**
"1. Query WAREHOUSE_METERING_HISTORY for top credit consumers. 2. Check for warehouses left running (no auto-suspend). 3. Find long queries in QUERY_HISTORY. 4. Identify users with most compute time. 5. Check for remote spilling. 6. Immediate fix: enable auto-suspend, kill runaway queries, add resource monitors. 7. Long-term: educate users, enforce standards via Terraform."

---

### Q: Design Snowflake architecture for e-commerce startup.

**Answer:**
"1. Landing schema: raw data from sources. 2. Staging schema: cleaned/typed data, transient tables. 3. Core schema: star schema facts/dimensions. 4. Marts schema: department-specific aggregates. 5. Warehouses: ETL_WH (MEDIUM), ANALYTICS_WH (SMALL), ADHOC_WH (X-SMALL). 6. Resource monitors per warehouse. 7. All managed via Terraform. 8. dbt for transformations. Start small, scale as needed."

---

### Q: How do you migrate from on-prem Oracle to Snowflake?

**Answer:**
"1. Extract: Use Fivetran/Airbyte or custom Python scripts. 2. Schema conversion: denormalize to star schema. 3. Load: bulk COPY INTO for historical, Snowpipe for ongoing. 4. Validation: row counts, checksums, sample queries. 5. Parallel run: both systems live while testing. 6. Cutover: switch applications to Snowflake. 7. Decommission: keep Oracle read-only for N months. Timeline: 2-4 months for typical setup."

---

### Q: How do you implement CDC from MySQL to Snowflake?

**Answer:**
"1. Use Debezium to capture MySQL binlog changes. 2. Stream to Kafka. 3. Kafka Connect Snowflake connector writes to staging. 4. Create Stream on staging table. 5. Task merges changes to target with MERGE statement. Alternative: Fivetran/Airbyte handles everything (easier, costs money). Pattern: source → CDC tool → Snowflake stage → Stream → Task → final table."

---

## **ADVANCED FEATURES**

### Q: What is Search Optimization Service?

**Answer:**
"Adds search access paths to tables for point lookups and substring/regex searches. Improves performance for selective queries (WHERE user_id = 'X' or WHERE email LIKE '%@domain.com'). Cost: storage overhead + maintenance compute. Enable on tables with point lookups that aren't clustered. Different from clustering - complementary."

---

### Q: What are Materialized Views in Snowflake?

**Answer:**
"Pre-computed query results automatically maintained. Snowflake refreshes automatically and transparently. Use for: expensive aggregations, frequently-run transformations, dashboard acceleration. Limitation: restricted SQL (no UDFs, no window functions). Cost: storage + maintenance compute. Check if query rewrites to use MV with Query Profile."

---

### Q: What is Dynamic Data Masking?

**Answer:**
"Automatically mask sensitive data based on user privileges. Define masking policy on column, specify masking functions by role. Example: show real SSN to HR role, mask to XXX-XX-1234 for others. No view duplication needed. Centrally managed. Use for: PII/PHI compliance, column-level security."

---

## **INTEGRATION & TOOLING**

### Q: How do you connect dbt to Snowflake?

**Answer:**
"Install dbt-snowflake adapter. Configure profiles.yml with account, warehouse, database, schema, credentials (user/password or key-pair). dbt compiles models to SQL, executes in Snowflake. Use incremental models with Snowflake merge. Define sources, models, tests. Run transformations in dedicated TRANSFORM_WH warehouse."

---

### Q: Best practices for Looker + Snowflake?

**Answer:**
"1. Dedicated LOOKER_WH warehouse (SMALL-MEDIUM). 2. Aggressive auto-suspend (5 min). 3. Persistent Derived Tables (PDTs) for complex metrics. 4. Use caching - remove time functions. 5. Symmetric aggregates in LookML. 6. Monitor with QUERY_HISTORY tagged by Looker. 7. Consider BI Engine reservation for Snowflake's BI optimization."

---

## **INTERVIEW TIPS**

### Key Points to Emphasize:
- ✅ Separation of storage and compute
- ✅ Cost optimization mindset (auto-suspend, right-sizing)
- ✅ Query performance (clustering, caching, Query Profile)
- ✅ Zero-copy cloning for dev/test
- ✅ Practical experience with ACCOUNT_USAGE views

### Common Follow-ups:
- "Have you used Snowflake in production?"
- "What was your biggest Snowflake cost optimization?"
- "How large were your Snowflake tables?"
- "What BI tools did you connect to Snowflake?"

### Answer Framework:
1. Direct answer (1-2 sentences)
2. Quick example or use case
3. One gotcha or best practice

**Stay concise, confident, and practical!** ✨
