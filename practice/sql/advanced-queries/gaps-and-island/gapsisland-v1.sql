-- ============================================================
-- GAPS AND ISLANDS — V1
-- ============================================================


-- ------------------------------------------------------------
-- Problem 1: Server Uptime Streaks
-- Find all periods where a server had at least 4 consecutive
-- days of healthy status.
-- ------------------------------------------------------------

WITH healthy_only AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY log_date) AS rn
    FROM server_health
    WHERE status = 'healthy'
),

islands AS (
    SELECT
        *,
        log_id - rn AS island_id   -- same value = consecutive healthy days
    FROM healthy_only
),

valid_islands AS (
    SELECT island_id
    FROM islands
    GROUP BY island_id
    HAVING COUNT(*) >= 4
)

SELECT
    i.log_id,
    i.log_date,
    i.status,
    i.cpu_usage
FROM islands i
JOIN valid_islands v ON i.island_id = v.island_id
ORDER BY i.log_date;


-- ------------------------------------------------------------
-- Problem 2: Stock Price Rally
-- Find all trading days that were part of a 3+ day rally
-- (closing price above 150). Uses day_id as the sequence key
-- since trading days are not calendar-consecutive.
-- ------------------------------------------------------------

WITH above_threshold AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date) AS rn
    FROM stock_prices
    WHERE closing_price > 150
),

islands AS (
    SELECT
        *,
        -- day_id - rn stays constant for consecutive trading days
        day_id - rn AS island_id
    FROM above_threshold
),

valid_islands AS (
    SELECT
        ticker,
        island_id,
        COUNT(*)        AS rally_days,
        MIN(trade_date) AS rally_start,
        MAX(trade_date) AS rally_end
    FROM islands
    GROUP BY ticker, island_id
    HAVING COUNT(*) >= 3
)

SELECT
    i.ticker,
    i.trade_date,
    i.closing_price,
    v.rally_start,
    v.rally_end,
    v.rally_days
FROM islands i
JOIN valid_islands v
    ON i.ticker = v.ticker
    AND i.island_id = v.island_id
ORDER BY i.trade_date;

-- Expected: Jan 8–11 (4-day rally at 158, 162, 170, 175)
