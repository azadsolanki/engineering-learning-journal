-- ============================================================
-- GAPS AND ISLANDS — V2
-- Multi-server, timestamp-based problems
-- ============================================================


-- ------------------------------------------------------------
-- Problem 1: Longest Consecutive Uptime Period (The Classic)
-- For each server, find the longest period where status was
-- 'healthy' or 'maintenance'. Logs are hourly so each gap
-- in sequence = 1 hour gap.
-- ------------------------------------------------------------

WITH uptime_rows AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY server_id ORDER BY log_date) AS rn
    FROM server_health
    WHERE status IN ('healthy', 'maintenance')
),

islands AS (
    SELECT
        server_id,
        log_date,
        -- subtract rn * 1 hour: same result = consecutive hourly entries
        log_date - (rn * INTERVAL '1 hour') AS island_id
    FROM uptime_rows
),

periods AS (
    SELECT
        server_id,
        island_id,
        MIN(log_date)               AS start_date,
        MAX(log_date)               AS end_date,
        COUNT(*)                    AS log_count,
        COUNT(*) * INTERVAL '1 hour' AS total_duration
    FROM islands
    GROUP BY server_id, island_id
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY server_id ORDER BY log_count DESC) AS rank_by_duration
    FROM periods
)

SELECT
    server_id,
    start_date,
    end_date,
    total_duration
FROM ranked
WHERE rank_by_duration = 1
ORDER BY server_id;


-- ------------------------------------------------------------
-- Problem 2: Consecutive High Resource Usage (The Anomaly Hunter)
-- Find all periods where Server 2 had cpu_usage > 90 for at
-- least 3 consecutive hours.
-- ------------------------------------------------------------

WITH high_cpu AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY log_date) AS rn
    FROM server_health
    WHERE server_id = 2
      AND cpu_usage > 90
),

islands AS (
    SELECT
        *,
        log_date - (rn * INTERVAL '1 hour') AS island_id
    FROM high_cpu
),

periods AS (
    SELECT
        island_id,
        MIN(log_date)              AS start_time,
        MAX(log_date)              AS end_time,
        COUNT(*)                   AS duration_hours,
        ROUND(AVG(cpu_usage), 2)   AS avg_cpu
    FROM islands
    GROUP BY island_id
    HAVING COUNT(*) >= 3
)

SELECT
    start_time,
    end_time,
    duration_hours,
    avg_cpu
FROM periods
ORDER BY start_time;

-- Expected: 13:00–15:00 on 2025-01-10 (3 hrs, avg ~95.67)
-- Note: 12:00 has cpu=90 which is NOT > 90, breaking the streak


-- ------------------------------------------------------------
-- Problem 3: State Reversals (The Downtime Analysis)
-- For Server 1, find every continuous 'down' and 'not-down'
-- period with its first and last log entry.
-- ------------------------------------------------------------

WITH server1 AS (
    SELECT
        log_id,
        log_date,
        status,
        CASE WHEN status = 'down' THEN 'down' ELSE 'not_down' END AS state
    FROM server_health
    WHERE server_id = 1
),

-- Mark rows where the state changes from the previous row
state_changes AS (
    SELECT
        *,
        CASE
            WHEN state != LAG(state) OVER (ORDER BY log_date)
              OR LAG(state) OVER (ORDER BY log_date) IS NULL
            THEN 1 ELSE 0
        END AS is_new_period
    FROM server1
),

-- Cumulative sum of change flags gives a unique group per period
grouped AS (
    SELECT
        *,
        SUM(is_new_period) OVER (ORDER BY log_date) AS period_grp
    FROM state_changes
)

SELECT
    state,
    MIN(log_date) AS period_start,
    MAX(log_date) AS period_end,
    COUNT(*)      AS entries
FROM grouped
GROUP BY state, period_grp
ORDER BY period_start;

-- Expected output:
-- not_down | 2025-01-01 | 2025-01-02 | 2   (healthy run)
-- down     | 2025-01-03 | 2025-01-03 | 1   (single down day)
-- not_down | 2025-01-04 | 2025-01-09 | 6   (healthy + maintenance)


-- ------------------------------------------------------------
-- Problem 4: Finding Collective Unstable Periods
-- Find all periods where 2+ distinct servers were simultaneously
-- 'unstable' for at least 6 consecutive hours.
-- ------------------------------------------------------------

WITH unstable_per_hour AS (
    -- At each timestamp, count how many servers are unstable
    SELECT
        log_date,
        COUNT(DISTINCT server_id) AS unstable_servers
    FROM server_health
    WHERE status = 'unstable'
    GROUP BY log_date
    HAVING COUNT(DISTINCT server_id) >= 2
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY log_date) AS rn
    FROM unstable_per_hour
),

islands AS (
    SELECT
        *,
        log_date - (rn * INTERVAL '1 hour') AS island_id
    FROM ranked
),

collective_periods AS (
    SELECT
        island_id,
        MIN(log_date)                AS start_time,
        MAX(log_date)                AS end_time,
        COUNT(*)                     AS duration_hours,
        MAX(unstable_servers)        AS peak_unstable_servers
    FROM islands
    GROUP BY island_id
    HAVING COUNT(*) >= 6
)

SELECT
    start_time,
    end_time,
    duration_hours,
    peak_unstable_servers
FROM collective_periods
ORDER BY start_time;

-- Expected: 11:00–16:00 on 2025-01-10 (6 hours, peak = 3 servers)
