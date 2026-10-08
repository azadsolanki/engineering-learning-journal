-- Test setup for the scripts in this folder. Works on a free trial account.
-- Run in a Snowsight worksheet. Replace <PASTE_PUBLIC_KEY_HERE> with the body of
-- rsa_key.pub (no BEGIN/END lines). See README.md, "Reproducing It".

USE ROLE ACCOUNTADMIN;

-- Small warehouse that suspends quickly to save credits
CREATE WAREHOUSE IF NOT EXISTS REPRO_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

CREATE ROLE IF NOT EXISTS REPRO_ROLE;
GRANT USAGE ON WAREHOUSE REPRO_WH TO ROLE REPRO_ROLE;

-- Sample data. If SHOW returns nothing, uncomment the CREATE.
SHOW DATABASES LIKE 'SNOWFLAKE_SAMPLE_DATA';
-- CREATE DATABASE SNOWFLAKE_SAMPLE_DATA FROM SHARE SFC_SAMPLES.SAMPLE_DATA;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE REPRO_ROLE;

-- Service user with key-pair auth (no MFA prompt, so scripts can log in).
-- Deliberately NO default warehouse: see "Finding 2" in README.md.
CREATE USER IF NOT EXISTS REPRO_USER
  TYPE = SERVICE
  DEFAULT_ROLE = REPRO_ROLE
  RSA_PUBLIC_KEY = '<PASTE_PUBLIC_KEY_HERE>';
GRANT ROLE REPRO_ROLE TO USER REPRO_USER;

-- Value for SF_ACCOUNT
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS sf_account;

-- Server-side timings after a run (pick a database in the worksheet context first).
-- SELECT query_id, query_type, LEFT(query_text, 60) AS query_text, start_time, end_time,
--        compilation_time, execution_time, total_elapsed_time
-- FROM TABLE(information_schema.query_history_by_user(
--        user_name => 'REPRO_USER', result_limit => 1000))
-- ORDER BY start_time;

-- Cleanup
-- DROP USER REPRO_USER;
-- DROP ROLE REPRO_ROLE;
-- DROP WAREHOUSE REPRO_WH;
