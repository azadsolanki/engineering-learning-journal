Retail Data Engineering SQL Master GuideThis guide provides a complete end-to-end environment for practicing SQL patterns common in retail data engineering interviews, specifically focusing on Modeling, Window Functions, and Complex Analytical Joins.1. The Environment: Schema (DDL) & Data (DML)Run this block in a PostgreSQL environment to set up your practice playground.-- ============================================================================
-- SCHEMA SETUP
-- ============================================================================

-- DIMENSION: PRODUCT (SCD Type 2)
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,       -- Surrogate Key
    product_id VARCHAR(50) NOT NULL,      -- Natural Key (SKU)
    product_name VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    product_material VARCHAR(100),
    effective_start_date DATE NOT NULL,Retail Data Engineering SQL Master Guide
    
    This guide provides a complete end-to-end environment for practicing SQL patterns common in retail data engineering interviews, specifically focusing on Modeling, Window Functions, and Complex Analytical Joins.
    
    1. The Environment: Schema (DDL) & Data (DML)
    
    Run this block in a PostgreSQL environment to set up your practice playground.
    
    -- ============================================================================
    -- SCHEMA SETUP
    -- ============================================================================
    
    -- DIMENSION: PRODUCT (SCD Type 2)
    CREATE TABLE dim_product (
        product_key SERIAL PRIMARY KEY,       -- Surrogate Key
        product_id VARCHAR(50) NOT NULL,      -- Natural Key (SKU)
        product_name VARCHAR(255) NOT NULL,
        category_id INT NOT NULL,
        product_material VARCHAR(100),
        effective_start_date DATE NOT NULL,
        effective_end_date DATE NOT NULL,
        is_current BOOLEAN DEFAULT TRUE
    );
    
    -- DIMENSION: CUSTOMER
    CREATE TABLE dim_customer (
        customer_id SERIAL PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        region VARCHAR(50),
        tier VARCHAR(20) DEFAULT 'Bronze'
    );
    
    -- FACT: SALES LINE ITEMS
    CREATE TABLE fact_sales (
        sale_id SERIAL PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL,
        product_key INT REFERENCES dim_product(product_key),
        customer_id INT REFERENCES dim_customer(customer_id),
        sale_date TIMESTAMP NOT NULL,
        quantity INT NOT NULL,
        revenue DECIMAL(12, 2) NOT NULL
    );
    
    -- FACT: DAILY STORE AGGREGATES
    CREATE TABLE fact_daily_sales (
        store_id INT NOT NULL,
        sale_date DATE NOT NULL,
        daily_revenue DECIMAL(15, 2) NOT NULL,
        PRIMARY KEY (store_id, sale_date)
    );
    
    -- FACTLESS FACT: PROMOTION COVERAGE
    CREATE TABLE fact_promotion_coverage (
        date_key DATE NOT NULL,
        product_key INT REFERENCES dim_product(product_key),
        promotion_id INT NOT NULL,
        PRIMARY KEY (date_key, product_key, promotion_id)
    );
    
    -- ============================================================================
    -- DATA SEEDING
    -- ============================================================================
    
    INSERT INTO dim_product (product_id, product_name, category_id, product_material, effective_start_date, effective_end_date, is_current) VALUES 
    ('TEE-01', 'Classic Crew', 1, '100% Cotton', '2023-01-01', '2024-01-01', FALSE),
    ('TEE-01', 'Classic Crew', 1, 'Organic Cotton', '2024-01-02', '9999-12-31', TRUE),
    ('JEAN-01', 'Slim Fit', 2, 'Denim', '2023-01-01', '9999-12-31', TRUE);
    
    INSERT INTO dim_customer (customer_name, region, tier) VALUES 
    ('Alice', 'North', 'Gold'), ('Bob', 'South', 'Silver'), ('Charlie', 'North', 'Bronze');
    
    INSERT INTO fact_daily_sales (store_id, sale_date, daily_revenue) VALUES
    (101, '2024-05-01', 1000), (101, '2024-05-02', 1200), (101, '2024-05-03', 900), (101, '2024-05-04', 1500),
    (102, '2024-05-01', 800), (102, '2024-05-02', 1100), (102, '2024-05-03', 1300);
    
    INSERT INTO fact_sales (order_id, product_key, customer_id, sale_date, quantity, revenue) VALUES
    ('ORD-1', 1, 1, '2023-06-15', 2, 40.00), ('ORD-2', 2, 1, '2024-02-20', 1, 25.00), ('ORD-3', 3, 2, '2024-03-01', 1, 60.00);
    
    
    2. Core Practice Questions (Warm-up)
    
    Q1: 7-Day Rolling Average
    
    Goal: Smooth out store volatility using window framing.
    
    SELECT 
        store_id, sale_date, daily_revenue,
        AVG(daily_revenue) OVER (
            PARTITION BY store_id ORDER BY sale_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as rolling_avg_7d
    FROM fact_daily_sales;
    
    
    Q2: Customer Lifetime Value (CLV) Rank
    
    Goal: Rank customers by total spend globally.
    
    SELECT 
        customer_id, SUM(revenue) as total_spend,
        DENSE_RANK() OVER (ORDER BY SUM(revenue) DESC) as clv_rank
    FROM fact_sales
    GROUP BY customer_id;
    
    
    3. Medium Difficulty Questions (Strategic Analysis)
    
    M1: Identifying "New" Product Revenue
    
    Question: Calculate total revenue for each product, but only for the sales that occurred while the product version was is_current = TRUE.
    
    SELECT p.product_name, SUM(s.revenue) as current_version_rev
    FROM fact_sales s
    JOIN dim_product p ON s.product_key = p.product_key
    WHERE p.is_current = TRUE
    GROUP BY p.product_name;
    
    
    M2: Month-over-Month (MoM) Growth
    
    Question: Calculate the percentage growth in total revenue from one month to the next.
    
    WITH MonthlySales AS (
        SELECT DATE_TRUNC('month', sale_date) as mth, SUM(revenue) as rev
        FROM fact_sales GROUP BY 1
    )
    SELECT mth, rev,
        LAG(rev) OVER (ORDER BY mth) as prev_rev,
        ((rev - LAG(rev) OVER (ORDER BY mth)) / NULLIF(LAG(rev) OVER (ORDER BY mth), 0)) * 100 as pct_growth
    FROM MonthlySales;
    
    
    M3: Top N Products per Region
    
    Question: Find the top 2 products (by revenue) for each customer region.
    
    WITH RegionalSales AS (
        SELECT c.region, p.product_id, SUM(s.revenue) as rev,
            ROW_NUMBER() OVER(PARTITION BY c.region ORDER BY SUM(s.revenue) DESC) as rank
        FROM fact_sales s
        JOIN dim_customer c ON s.customer_id = c.customer_id
        JOIN dim_product p ON s.product_key = p.product_key
        GROUP BY 1, 2
    )
    SELECT * FROM RegionalSales WHERE rank <= 2;
    
    
    4. Difficult Questions (Foundational Data Engineering)
    
    D1: Gap Analysis (Consecutive Drops)
    
    Question: Find all stores that had a "revenue drop" (current day revenue < previous day revenue) for 3 or more consecutive days.
    
    WITH RevenueChanges AS (
        SELECT store_id, sale_date, daily_revenue,
            CASE WHEN daily_revenue < LAG(daily_revenue) OVER(PARTITION BY store_id ORDER BY sale_date) 
                 THEN 1 ELSE 0 END as is_drop
        FROM fact_daily_sales
    ),
    GroupedDrops AS (
        SELECT *,
            SUM(is_drop) OVER(PARTITION BY store_id ORDER BY sale_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as consecutive_drops
        FROM RevenueChanges
    )
    SELECT DISTINCT store_id FROM GroupedDrops WHERE consecutive_drops >= 3;
    
    
    D2: Promotion Effectiveness (The Factless Fact Join)
    
    Question: Calculate the "Conversion Rate" of promotions: (Unique products sold during promotion / Total products eligible).
    
    SELECT 
        pc.promotion_id,
        COUNT(DISTINCT s.product_key)::float / NULLIF(COUNT(DISTINCT pc.product_key), 0) as conversion_rate
    FROM fact_promotion_coverage pc
    LEFT JOIN fact_sales s ON pc.product_key = s.product_key 
        AND pc.date_key = CAST(s.sale_date AS DATE)
    GROUP BY pc.promotion_id;
    
    
    D3: Data Quality (Detecting SCD2 Overlaps)
    
    Question: Detect if any product in dim_product has overlapping dates (integrity check).
    
    SELECT p1.product_id, p1.product_key as record_a, p2.product_key as record_b
    FROM dim_product p1
    JOIN dim_product p2 ON p1.product_id = p2.product_id AND p1.product_key <> p2.product_key
    WHERE p1.effective_start_date BETWEEN p2.effective_start_date AND p2.effective_end_date;

    effective_end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT TRUE
);

-- DIMENSION: CUSTOMER
CREATE TABLE dim_customer (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    tier VARCHAR(20) DEFAULT 'Bronze'
);

-- FACT: SALES LINE ITEMS
CREATE TABLE fact_sales (
    sale_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_key INT REFERENCES dim_product(product_key),
    customer_id INT REFERENCES dim_customer(customer_id),
    sale_date TIMESTAMP NOT NULL,
    quantity INT NOT NULL,
    revenue DECIMAL(12, 2) NOT NULL
);

-- FACT: DAILY STORE AGGREGATES
CREATE TABLE fact_daily_sales (
    store_id INT NOT NULL,
    sale_date DATE NOT NULL,
    daily_revenue DECIMAL(15, 2) NOT NULL,
    PRIMARY KEY (store_id, sale_date)
);

-- FACTLESS FACT: PROMOTION COVERAGE
CREATE TABLE fact_promotion_coverage (
    date_key DATE NOT NULL,
    product_key INT REFERENCES dim_product(product_key),
    promotion_id INT NOT NULL,
    PRIMARY KEY (date_key, product_key, promotion_id)
);

-- ============================================================================
-- DATA SEEDING
-- ============================================================================

INSERT INTO dim_product (product_id, product_name, category_id, product_material, effective_start_date, effective_end_date, is_current) VALUES 
('TEE-01', 'Classic Crew', 1, '100% Cotton', '2023-01-01', '2024-01-01', FALSE),
('TEE-01', 'Classic Crew', 1, 'Organic Cotton', '2024-01-02', '9999-12-31', TRUE),
('JEAN-01', 'Slim Fit', 2, 'Denim', '2023-01-01', '9999-12-31', TRUE);

INSERT INTO dim_customer (customer_name, region, tier) VALUES 
('Alice', 'North', 'Gold'), ('Bob', 'South', 'Silver'), ('Charlie', 'North', 'Bronze');

INSERT INTO fact_daily_sales (store_id, sale_date, daily_revenue) VALUES
(101, '2024-05-01', 1000), (101, '2024-05-02', 1200), (101, '2024-05-03', 900), (101, '2024-05-04', 1500),
(102, '2024-05-01', 800), (102, '2024-05-02', 1100), (102, '2024-05-03', 1300);

INSERT INTO fact_sales (order_id, product_key, customer_id, sale_date, quantity, revenue) VALUES
('ORD-1', 1, 1, '2023-06-15', 2, 40.00), ('ORD-2', 2, 1, '2024-02-20', 1, 25.00), ('ORD-3', 3, 2, '2024-03-01', 1, 60.00);
2. Core Practice Questions (Warm-up)Q1: 7-Day Rolling AverageGoal: Smooth out store volatility using window framing.SELECT 
    store_id, sale_date, daily_revenue,
    AVG(daily_revenue) OVER (
        PARTITION BY store_id ORDER BY sale_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as rolling_avg_7d
FROM fact_daily_sales;
Q2: Customer Lifetime Value (CLV) RankGoal: Rank customers by total spend globally.SELECT 
    customer_id, SUM(revenue) as total_spend,
    DENSE_RANK() OVER (ORDER BY SUM(revenue) DESC) as clv_rank
FROM fact_sales
GROUP BY customer_id;
3. Medium Difficulty Questions (Strategic Analysis)M1: Identifying "New" Product RevenueQuestion: Calculate total revenue for each product, but only for the sales that occurred while the product version was is_current = TRUE.SELECT p.product_name, SUM(s.revenue) as current_version_rev
FROM fact_sales s
JOIN dim_product p ON s.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_name;
M2: Month-over-Month (MoM) GrowthQuestion: Calculate the percentage growth in total revenue from one month to the next.WITH MonthlySales AS (
    SELECT DATE_TRUNC('month', sale_date) as mth, SUM(revenue) as rev
    FROM fact_sales GROUP BY 1
)
SELECT mth, rev,
    LAG(rev) OVER (ORDER BY mth) as prev_rev,
    ((rev - LAG(rev) OVER (ORDER BY mth)) / NULLIF(LAG(rev) OVER (ORDER BY mth), 0)) * 100 as pct_growth
FROM MonthlySales;
M3: Top N Products per RegionQuestion: Find the top 2 products (by revenue) for each customer region.WITH RegionalSales AS (
    SELECT c.region, p.product_id, SUM(s.revenue) as rev,
        ROW_NUMBER() OVER(PARTITION BY c.region ORDER BY SUM(s.revenue) DESC) as rank
    FROM fact_sales s
    JOIN dim_customer c ON s.customer_id = c.customer_id
    JOIN dim_product p ON s.product_key = p.product_key
    GROUP BY 1, 2
)
SELECT * FROM RegionalSales WHERE rank <= 2;
4. Difficult Questions (Foundational Data Engineering)D1: Gap Analysis (Consecutive Drops)Question: Find all stores that had a "revenue drop" (current day revenue < previous day revenue) for 3 or more consecutive days.WITH RevenueChanges AS (
    SELECT store_id, sale_date, daily_revenue,
        CASE WHEN daily_revenue < LAG(daily_revenue) OVER(PARTITION BY store_id ORDER BY sale_date) 
             THEN 1 ELSE 0 END as is_drop
    FROM fact_daily_sales
),
GroupedDrops AS (
    SELECT *,
        SUM(is_drop) OVER(PARTITION BY store_id ORDER BY sale_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as consecutive_drops
    FROM RevenueChanges
)
SELECT DISTINCT store_id FROM GroupedDrops WHERE consecutive_drops >= 3;
D2: Promotion Effectiveness (The Factless Fact Join)Question: Calculate the "Conversion Rate" of promotions: (Unique products sold during promotion / Total products eligible).SELECT 
    pc.promotion_id,
    COUNT(DISTINCT s.product_key)::float / NULLIF(COUNT(DISTINCT pc.product_key), 0) as conversion_rate
FROM fact_promotion_coverage pc
LEFT JOIN fact_sales s ON pc.product_key = s.product_key 
    AND pc.date_key = CAST(s.sale_date AS DATE)
GROUP BY pc.promotion_id;
D3: Data Quality (Detecting SCD2 Overlaps)Question: Detect if any product in dim_product has overlapping dates (integrity check).SELECT p1.product_id, p1.product_key as record_a, p2.product_key as record_b
FROM dim_product p1
JOIN dim_product p2 ON p1.product_id = p2.product_id AND p1.product_key <> p2.product_key
WHERE p1.effective_start_date BETWEEN p2.effective_start_date AND p2.effective_end_date;
