"""
Seed DuckDB with sample retail analytics data that mirrors the dbt mart tables.

Tables:
  dim_users          200 customers
  dim_products       100 products
  fct_orders         2000 orders (2023-2024)
  fct_daily_revenue  daily rollup from orders

Usage:
    python seed.py
"""

import random
from datetime import date, timedelta, datetime
from collections import defaultdict
from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = str(Path(__file__).parent.parent / "retail_analytics.duckdb")

random.seed(42)

GENDERS = ["M", "F"]
AGE_GROUPS = ["18-25", "26-35", "36-45", "46-55", "55+"]
GENERATIONS = {
    "18-25": "Gen Z", "26-35": "Millennial",
    "36-45": "Millennial", "46-55": "Gen X", "55+": "Boomer",
}
COUNTRIES = ["USA"] * 7 + ["UK", "Canada", "Germany"]
REGIONS = {"USA": "North America", "Canada": "North America", "UK": "Europe", "Germany": "Europe"}
TRAFFIC_SOURCES = ["Search", "Social", "Email", "Direct", "Display"]
ACQ_CHANNELS = {
    "Search": "Organic Search", "Social": "Social Media",
    "Email": "Email Marketing", "Direct": "Direct", "Display": "Paid Display",
}
CATEGORIES = [
    ("Jeans", "Apparel"), ("Tops & Tees", "Apparel"), ("Dresses", "Apparel"),
    ("Shorts", "Apparel"), ("Sweaters", "Apparel"), ("Sleep & Lounge", "Apparel"),
    ("Running Shoes", "Footwear"), ("Casual Shoes", "Footwear"), ("Boots", "Footwear"),
    ("Bags", "Accessories"), ("Hats & Caps", "Accessories"), ("Socks", "Accessories"),
]
BRANDS = ["Calvin Klein", "Levi's", "Nike", "Adidas", "H&M", "Zara",
          "Tommy Hilfiger", "Gap", "North Face", "Patagonia"]
DEPARTMENTS = ["Men", "Women", "Kids"]
ORDER_STATUSES = ["Complete"] * 6 + ["Shipped"] * 2 + ["Processing"] + ["Cancelled"]
TIMES_OF_DAY = ["Morning", "Afternoon", "Evening", "Night"]


def make_users(n=200):
    rows = []
    for i in range(1, n + 1):
        ag = random.choice(AGE_GROUPS)
        country = random.choice(COUNTRIES)
        ts = random.choice(TRAFFIC_SOURCES)
        completed = random.randint(0, 15)
        total = completed + random.randint(0, 3)
        ltv = round(completed * random.uniform(50, 350), 2)
        aov = round(ltv / completed, 2) if completed > 0 else 0.0
        days_last = random.randint(1, 600) if completed > 0 else 999999

        if ltv >= 1000:       vseg = "VIP"
        elif completed >= 5:  vseg = "Loyal"
        elif completed >= 2:  vseg = "Regular"
        elif completed >= 1:  vseg = "New"
        else:                 vseg = "Prospect"

        if days_last <= 90:         aseg = "Active"
        elif days_last <= 180:      aseg = "At Risk"
        elif days_last <= 365:      aseg = "Dormant"
        elif days_last < 999999:    aseg = "Churned"
        else:                       aseg = "Prospect"

        rows.append({
            "user_id": i,
            "first_name": f"First{i}",
            "last_name": f"Last{i}",
            "email": f"user{i}@example.com",
            "age": int(ag.rstrip("+").split("-")[0]) + random.randint(0, 7),
            "age_group": ag,
            "generation": GENERATIONS[ag],
            "gender": random.choice(GENDERS),
            "country": country,
            "region": REGIONS.get(country, "International"),
            "is_domestic": country == "USA",
            "traffic_source": ts,
            "acquisition_channel": ACQ_CHANNELS[ts],
            "registration_date": date(2020, 1, 1) + timedelta(days=random.randint(0, 1460)),
            "total_orders": total,
            "completed_orders": completed,
            "lifetime_value": ltv,
            "avg_order_value": aov,
            "days_since_last_order": days_last,
            "value_segment": vseg,
            "activity_segment": aseg,
            "recency_score": 5 if days_last <= 30 else 4 if days_last <= 90 else 3 if days_last <= 180 else 2 if days_last <= 365 else 1,
            "frequency_score": 5 if completed >= 10 else 4 if completed >= 5 else 3 if completed >= 3 else 2 if completed >= 2 else 1,
            "monetary_score": 5 if ltv >= 1000 else 4 if ltv >= 500 else 3 if ltv >= 200 else 2 if ltv >= 100 else 1,
        })
    return rows


def make_products(n=100):
    price_ranges = {
        "Budget": (10.0, 50.0),
        "Mid-Range": (50.0, 150.0),
        "Premium": (150.0, 300.0),
        "Luxury": (300.0, 1000.0),
    }
    rows = []
    for i in range(1, n + 1):
        cat, cat_group = random.choice(CATEGORIES)
        brand = random.choice(BRANDS)
        price_cat = random.choice(list(price_ranges))
        lo, hi = price_ranges[price_cat]
        retail = round(random.uniform(lo, hi), 2)
        cost = round(retail * random.uniform(0.30, 0.55), 2)
        margin_pct = round((retail - cost) / retail * 100, 2)
        units = random.randint(0, 500)
        total_rev = round(units * retail * random.uniform(0.8, 1.0), 2)
        total_profit = round(total_rev * margin_pct / 100, 2)
        units_ret = int(units * random.uniform(0.0, 0.15))
        return_rate = round(units_ret / units * 100, 2) if units > 0 else 0.0
        rev_90d = round(total_rev * random.uniform(0.05, 0.3), 2)

        if total_rev >= 50000:   perf = "Star"
        elif total_rev >= 20000: perf = "High Performer"
        elif total_rev >= 5000:  perf = "Good Performer"
        elif total_rev >= 1000:  perf = "Average Performer"
        elif total_rev > 0:      perf = "Slow Mover"
        else:                    perf = "No Sales"

        if rev_90d > 1000:   inv = "Hot"
        elif rev_90d > 100:  inv = "Moving"
        elif rev_90d > 0:    inv = "Slow"
        else:                inv = "Dead Stock"

        rows.append({
            "product_id": i,
            "product_name": f"{brand} {cat} {i}",
            "category": cat,
            "category_group": cat_group,
            "brand": brand,
            "department": random.choice(DEPARTMENTS),
            "retail_price": retail,
            "product_cost": cost,
            "margin_percentage": margin_pct,
            "price_category": price_cat,
            "total_units_sold": units,
            "total_revenue": total_rev,
            "total_gross_profit": total_profit,
            "return_rate": return_rate,
            "performance_tier": perf,
            "inventory_status": inv,
        })
    return rows


def make_orders(users, n=2000):
    start = datetime(2023, 1, 1)
    user_order_count = {}
    rows = []

    for i in range(1, n + 1):
        user = random.choice(users)
        uid = user["user_id"]
        user_order_count[uid] = user_order_count.get(uid, 0) + 1
        order_num = user_order_count[uid]

        order_dt = start + timedelta(days=random.randint(0, 729))
        status = random.choice(ORDER_STATUSES)
        total = round(random.uniform(20.0, 500.0), 2)
        has_returns = random.random() < 0.10
        returned = round(total * random.uniform(0.1, 0.5), 2) if has_returns else 0.0
        gross_profit = round(total * random.uniform(0.30, 0.55), 2)
        month = order_dt.month
        quarter = (month - 1) // 3 + 1

        if total >= 200:   size_cat = "Large"
        elif total >= 100: size_cat = "Medium"
        elif total >= 50:  size_cat = "Small"
        else:              size_cat = "Micro"

        if month in (11, 12):  season = "Holiday Season"
        elif month in (6, 7, 8): season = "Summer"
        elif month in (3, 4, 5): season = "Spring"
        else:                  season = "Regular Season"

        rows.append({
            "order_id": i,
            "user_id": uid,
            "order_date": order_dt,
            "order_status": status,
            "order_total": total,
            "net_order_total": round(total - returned, 2),
            "total_gross_profit": gross_profit,
            "returned_amount": returned,
            "total_line_items": random.randint(1, 8),
            "customer_gender": user["gender"],
            "customer_age_group": user["age_group"],
            "customer_country": user["country"],
            "customer_region": user["region"],
            "is_domestic_customer": user["is_domestic"],
            "is_weekend": order_dt.weekday() >= 5,
            "order_time_of_day": random.choice(TIMES_OF_DAY),
            "order_month": month,
            "order_quarter": quarter,
            "order_year": order_dt.year,
            "is_first_order": order_num == 1,
            "customer_order_number": order_num,
            "customer_segment_at_order": user["value_segment"],
            "order_size_category": size_cat,
            "seasonal_period": season,
            "has_returns": has_returns,
            "delivery_days": random.randint(1, 14) if status in ("Complete", "Shipped") else None,
        })
    return rows


def make_daily_revenue(orders):
    daily = defaultdict(lambda: {
        "total_revenue": 0.0, "net_revenue": 0.0, "total_gross_profit": 0.0,
        "total_orders": 0, "customers": set(), "new_customers": 0,
        "returning_customers": 0, "total_items": 0,
    })

    for o in orders:
        if o["order_status"] not in ("Complete", "Shipped", "Processing"):
            continue
        d = o["order_date"].date()
        daily[d]["total_revenue"] += o["order_total"]
        daily[d]["net_revenue"] += o["net_order_total"]
        daily[d]["total_gross_profit"] += o["total_gross_profit"]
        daily[d]["total_orders"] += 1
        daily[d]["customers"].add(o["user_id"])
        daily[d]["total_items"] += o["total_line_items"]
        if o["is_first_order"]:
            daily[d]["new_customers"] += 1
        else:
            daily[d]["returning_customers"] += 1

    rows = []
    rev_window = []
    for d in sorted(daily):
        rec = daily[d]
        rev = round(rec["total_revenue"], 2)
        rev_window.append(rev)
        avg_30 = round(sum(rev_window[-30:]) / min(len(rev_window), 30), 2)
        avg_7 = round(sum(rev_window[-7:]) / min(len(rev_window), 7), 2)
        tot = rec["total_orders"]
        gp = round(rec["total_gross_profit"], 2)

        if rev > avg_30 * 1.2:    perf = "High Performance"
        elif rev < avg_30 * 0.8:  perf = "Low Performance"
        else:                     perf = "Normal Performance"

        rows.append({
            "revenue_date": d,
            "total_revenue": rev,
            "net_revenue": round(rec["net_revenue"], 2),
            "total_gross_profit": gp,
            "avg_order_value": round(rev / tot, 2) if tot > 0 else 0.0,
            "total_orders": tot,
            "unique_customers": len(rec["customers"]),
            "new_customers": rec["new_customers"],
            "returning_customers": rec["returning_customers"],
            "total_items_sold": rec["total_items"],
            "gross_margin_rate": round(gp / rev, 4) if rev > 0 else 0.0,
            "return_rate": round(random.uniform(0.02, 0.12), 4),
            "cancellation_rate": round(random.uniform(0.01, 0.08), 4),
            "revenue_7day_avg": avg_7,
            "revenue_30day_avg": avg_30,
            "daily_performance_status": perf,
        })
    return rows


def seed(db_path: str = DB_PATH):
    conn = duckdb.connect(db_path)

    users = make_users(200)
    products = make_products(100)
    orders = make_orders(users, 2000)
    daily_rev = make_daily_revenue(orders)

    df_users = pd.DataFrame(users)
    df_products = pd.DataFrame(products)
    df_orders = pd.DataFrame(orders)
    df_daily = pd.DataFrame(daily_rev)

    conn.register("df_users", df_users)
    conn.register("df_products", df_products)
    conn.register("df_orders", df_orders)
    conn.register("df_daily", df_daily)

    conn.execute("DROP TABLE IF EXISTS dim_users;         CREATE TABLE dim_users AS SELECT * FROM df_users")
    conn.execute("DROP TABLE IF EXISTS dim_products;      CREATE TABLE dim_products AS SELECT * FROM df_products")
    conn.execute("DROP TABLE IF EXISTS fct_orders;        CREATE TABLE fct_orders AS SELECT * FROM df_orders")
    conn.execute("DROP TABLE IF EXISTS fct_daily_revenue; CREATE TABLE fct_daily_revenue AS SELECT * FROM df_daily")

    conn.close()
    print(f"Seeded {db_path}:")
    print(f"  dim_users          {len(users)} rows")
    print(f"  dim_products       {len(products)} rows")
    print(f"  fct_orders         {len(orders)} rows")
    print(f"  fct_daily_revenue  {len(daily_rev)} rows")


if __name__ == "__main__":
    seed()
