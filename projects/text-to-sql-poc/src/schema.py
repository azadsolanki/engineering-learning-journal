"""
Schema context for the retail analytics text-to-SQL chain.

DDL mirrors the dbt mart layer from retail-analytics-framework:
  - dim_users      (from models/marts/dim_users.sql)
  - dim_products   (from models/marts/dim_products.sql)
  - fct_orders     (from models/marts/fct_orders.sql)
  - fct_daily_revenue (from models/marts/fct_daily_revenue.sql)

SEMANTIC_CONTEXT maps business terms to SQL expressions,
derived from models/semantic/ (sem_orders.yml, sem_customers.yml,
sem_products.yml, metrics.yml).
"""

DDL = """
CREATE TABLE dim_users (
    user_id              INTEGER,
    first_name           VARCHAR,
    last_name            VARCHAR,
    email                VARCHAR,
    age                  INTEGER,
    age_group            VARCHAR,         -- '18-25', '26-35', '36-45', '46-55', '55+'
    generation           VARCHAR,         -- 'Gen Z', 'Millennial', 'Gen X', 'Boomer'
    gender               VARCHAR,         -- 'M', 'F'
    country              VARCHAR,
    region               VARCHAR,
    is_domestic          BOOLEAN,
    traffic_source       VARCHAR,
    acquisition_channel  VARCHAR,
    registration_date    DATE,
    total_orders         INTEGER,
    completed_orders     INTEGER,
    lifetime_value       DECIMAL(10,2),
    avg_order_value      DECIMAL(10,2),
    days_since_last_order INTEGER,
    value_segment        VARCHAR,         -- 'VIP', 'Loyal', 'Regular', 'New', 'Prospect'
    activity_segment     VARCHAR,         -- 'Active', 'At Risk', 'Dormant', 'Churned', 'Prospect'
    recency_score        INTEGER,         -- 1-5
    frequency_score      INTEGER,         -- 1-5
    monetary_score       INTEGER          -- 1-5
);

CREATE TABLE dim_products (
    product_id           INTEGER,
    product_name         VARCHAR,
    category             VARCHAR,
    category_group       VARCHAR,         -- 'Apparel', 'Footwear', 'Accessories'
    brand                VARCHAR,
    department           VARCHAR,         -- 'Men', 'Women', 'Kids'
    retail_price         DECIMAL(10,2),
    product_cost         DECIMAL(10,2),
    margin_percentage    DECIMAL(5,2),
    price_category       VARCHAR,         -- 'Luxury', 'Premium', 'Mid-Range', 'Budget'
    total_units_sold     INTEGER,
    total_revenue        DECIMAL(12,2),
    total_gross_profit   DECIMAL(12,2),
    return_rate          DECIMAL(5,2),
    performance_tier     VARCHAR,         -- 'Star', 'High Performer', 'Good Performer', 'Average Performer', 'Slow Mover'
    inventory_status     VARCHAR          -- 'Hot', 'Moving', 'Slow', 'Dead Stock'
);

CREATE TABLE fct_orders (
    order_id                    INTEGER,
    user_id                     INTEGER,   -- FK → dim_users.user_id
    order_date                  TIMESTAMP,
    order_status                VARCHAR,   -- 'Complete', 'Shipped', 'Processing', 'Cancelled', 'Returned'
    order_total                 DECIMAL(10,2),
    net_order_total             DECIMAL(10,2),   -- order_total minus returned_amount
    total_gross_profit          DECIMAL(10,2),
    returned_amount             DECIMAL(10,2),
    total_line_items            INTEGER,
    customer_gender             VARCHAR,
    customer_age_group          VARCHAR,
    customer_country            VARCHAR,
    customer_region             VARCHAR,
    is_domestic_customer        BOOLEAN,
    is_weekend                  BOOLEAN,
    order_time_of_day           VARCHAR,   -- 'Morning', 'Afternoon', 'Evening', 'Night'
    order_month                 INTEGER,
    order_quarter               INTEGER,
    order_year                  INTEGER,
    is_first_order              BOOLEAN,
    customer_order_number       INTEGER,
    customer_segment_at_order   VARCHAR,   -- 'VIP', 'Loyal', 'Regular', 'New'
    order_size_category         VARCHAR,   -- 'Large' (>=$200), 'Medium' (>=$100), 'Small' (>=$50), 'Micro'
    seasonal_period             VARCHAR,   -- 'Holiday Season', 'Summer', 'Spring', 'Regular Season'
    has_returns                 BOOLEAN,
    delivery_days               INTEGER
);

CREATE TABLE fct_daily_revenue (
    revenue_date             DATE,
    total_revenue            DECIMAL(12,2),
    net_revenue              DECIMAL(12,2),
    total_gross_profit       DECIMAL(12,2),
    avg_order_value          DECIMAL(10,2),
    total_orders             INTEGER,
    unique_customers         INTEGER,
    new_customers            INTEGER,
    returning_customers      INTEGER,
    total_items_sold         INTEGER,
    gross_margin_rate        DECIMAL(5,4),
    return_rate              DECIMAL(5,4),
    cancellation_rate        DECIMAL(5,4),
    revenue_7day_avg         DECIMAL(12,2),
    revenue_30day_avg        DECIMAL(12,2),
    daily_performance_status VARCHAR       -- 'High Performance', 'Normal Performance', 'Low Performance'
);
"""

SEMANTIC_CONTEXT = """
-- ── Metric definitions (from metrics.yml) ──────────────────────────────────
-- revenue          : SUM(order_total) FROM fct_orders
-- net_revenue      : SUM(net_order_total) FROM fct_orders  -- excludes returns
-- gross_profit     : SUM(total_gross_profit) FROM fct_orders
-- gross_margin_%   : gross_profit / NULLIF(revenue, 0) * 100
-- aov              : AVG(order_total) FROM fct_orders
-- return_rate_%    : SUM(returned_amount) / NULLIF(SUM(order_total), 0) * 100
-- active_customers : COUNT(DISTINCT user_id) FROM fct_orders
-- customer_ltv     : AVG(lifetime_value) FROM dim_users

-- ── Join keys ───────────────────────────────────────────────────────────────
-- fct_orders.user_id = dim_users.user_id

-- ── Table selection guide ────────────────────────────────────────────────────
-- fct_daily_revenue → time-series, trend, daily/weekly/monthly revenue queries
-- fct_orders        → order-level, segment, customer, or product-mix queries
-- dim_users         → customer attributes, segments, RFM analysis
-- dim_products      → product catalog, category, brand, margin analysis

-- ── Enum values ─────────────────────────────────────────────────────────────
-- value_segment     : 'VIP' (LTV >= $1000), 'Loyal' (5+ orders), 'Regular' (2+ orders), 'New' (1 order)
-- activity_segment  : 'Active' (<=90 days), 'At Risk' (<=180), 'Dormant' (<=365), 'Churned'
-- order_size_category : 'Large' (>=$200), 'Medium' (>=$100), 'Small' (>=$50), 'Micro'
-- price_category    : 'Luxury', 'Premium', 'Mid-Range', 'Budget'
-- category_group    : 'Apparel', 'Footwear', 'Accessories'
-- seasonal_period   : 'Holiday Season' (Nov-Dec), 'Summer' (Jun-Aug), 'Spring' (Mar-May)
-- performance_tier  : 'Star' (>=$50k), 'High Performer' (>=$20k), 'Good Performer' (>=$5k)
"""
