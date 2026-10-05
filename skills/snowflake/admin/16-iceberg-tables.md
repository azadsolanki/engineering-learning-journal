# Snowflake Iceberg Tables & External Volumes

> Keeping data in your own object storage in open Apache Iceberg format, readable by Snowflake *and* by other engines (Spark, Trino).

See also: [`skills/iceberg`](../../iceberg) and [`skills/trino`](../../trino).

---

## Two Catalog Options

| | Snowflake-managed catalog | External catalog (Glue, Open Catalog / Polaris, REST) |
|:---|:---|:---|
| Who writes | Snowflake | Usually another engine |
| Snowflake access | Read + write | Read-only (plus writes for some REST catalogs) |
| Maintenance (compaction, snapshots) | Automatic | Your responsibility |
| Good for | Snowflake-first lakehouse that other engines read | Data owned by Spark/Trino pipelines |

> **💡 Billing:** Storage is billed by **your cloud provider**, not Snowflake. Compute is billed by Snowflake as usual.

---

## Step 1: External Volume

```sql
USE ROLE ACCOUNTADMIN;
CREATE EXTERNAL VOLUME lake_vol
  STORAGE_LOCATIONS = (
    (
      NAME = 'us-west-2-lake'
      STORAGE_PROVIDER = 'S3'
      STORAGE_BASE_URL = 's3://acme-lake/iceberg/'
      STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-lake-rw'
    )
  )
  ALLOW_WRITES = TRUE;

DESC EXTERNAL VOLUME lake_vol;
-- Add STORAGE_AWS_IAM_USER_ARN + STORAGE_AWS_EXTERNAL_ID to the IAM trust policy

SELECT SYSTEM$VERIFY_EXTERNAL_VOLUME('lake_vol');   -- tests read/write/list/delete

GRANT USAGE ON EXTERNAL VOLUME lake_vol TO ROLE data_engineer;
```

---

## Step 2a: Snowflake-Managed Iceberg Table

```sql
CREATE ICEBERG TABLE analytics.events_iceberg (
  event_id   STRING,
  user_id    STRING,
  event_type STRING,
  event_ts   TIMESTAMP_NTZ(6)
)
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'lake_vol'
  BASE_LOCATION = 'analytics/events/';

INSERT INTO analytics.events_iceberg SELECT ... FROM raw.events;
```

Other engines can read it through **Snowflake Horizon's Iceberg REST catalog** endpoint, or from the metadata files under `BASE_LOCATION`.

## Step 2b: Externally Managed (AWS Glue)

```sql
CREATE CATALOG INTEGRATION glue_cat
  CATALOG_SOURCE = GLUE
  CATALOG_NAMESPACE = 'lake_db'
  TABLE_FORMAT = ICEBERG
  GLUE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-glue-reader'
  GLUE_CATALOG_ID = '123456789012'
  GLUE_REGION = 'us-west-2'
  ENABLED = TRUE;

CREATE ICEBERG TABLE analytics.clicks
  EXTERNAL_VOLUME = 'lake_vol'
  CATALOG = 'glue_cat'
  CATALOG_TABLE_NAME = 'clicks';

-- Pick up new snapshots written by Spark/Trino
ALTER ICEBERG TABLE analytics.clicks REFRESH;
```

> **💡 Tip:** Set `AUTO_REFRESH = TRUE` on externally managed tables (supported catalogs) instead of scheduling manual refreshes.

---

## Admin Gotchas

> **⚠️** Iceberg tables have no Fail-safe, and Time Travel depends on the snapshots kept in the catalog.

> **⚠️** Don't let two catalogs write to the same table. Exactly one catalog owns each table.

> **⚠️** Lock down the bucket. Anyone with S3 access can read the Parquet files directly, bypassing Snowflake masking and row access policies.

```sql
SHOW ICEBERG TABLES IN DATABASE analytics;
SELECT SYSTEM$GET_ICEBERG_TABLE_INFORMATION('analytics.events_iceberg');   -- metadata location
```

## Checklist

- [ ] External volume verified with `SYSTEM$VERIFY_EXTERNAL_VOLUME`
- [ ] One clear owner catalog per table
- [ ] Bucket access restricted (policies don't apply outside Snowflake)
- [ ] Refresh strategy set for externally managed tables
