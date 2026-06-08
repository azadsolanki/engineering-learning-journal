"""Generates a synthetic e-commerce orders dataset for the pipeline."""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_CUSTOMERS = 200
N_ORDERS = 2000

rng = np.random.default_rng(SEED)

customer_ids = rng.integers(1000, 1000 + N_CUSTOMERS, size=N_ORDERS)
product_categories = rng.choice(
    ["electronics", "clothing", "books", "home", "sports"], size=N_ORDERS
)
order_amounts = rng.exponential(scale=80, size=N_ORDERS).round(2)
order_dates = pd.date_range("2024-01-01", periods=N_ORDERS, freq="2h")
return_flag = (rng.random(N_ORDERS) < 0.08).astype(int)
discount_pct = rng.choice([0, 5, 10, 15, 20], size=N_ORDERS)

df = pd.DataFrame(
    {
        "order_id": range(1, N_ORDERS + 1),
        "customer_id": customer_ids,
        "category": product_categories,
        "order_amount": order_amounts,
        "order_date": order_dates,
        "returned": return_flag,
        "discount_pct": discount_pct,
    }
)

out = Path(__file__).parent.parent / "data" / "orders.csv"
df.to_csv(out, index=False)
print(f"Generated {len(df)} rows → {out}")
