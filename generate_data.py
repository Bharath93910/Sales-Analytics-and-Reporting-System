import calendar
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ORDERS = 5200
N_CUSTOMERS = 400
START_YEAR, END_YEAR = 2024, 2025

# name, category, unit_price (INR), unit_cost (INR)
PRODUCTS = [
    ("Wireless Mouse", "Electronics", 799, 450),
    ("Bluetooth Speaker", "Electronics", 2499, 1500),
    ("Headphones", "Electronics", 3499, 2000),
    ("Power Bank", "Electronics", 1499, 850),
    ("Smart Watch", "Electronics", 5999, 3800),
    ("Air Fryer", "Home & Kitchen", 6499, 4200),
    ("Mixer Grinder", "Home & Kitchen", 3299, 2100),
    ("Water Bottle Set", "Home & Kitchen", 699, 330),
    ("Non-stick Cookware", "Home & Kitchen", 2799, 1700),
    ("Electric Kettle", "Home & Kitchen", 1199, 700),
    ("Running Shoes", "Fashion", 2999, 1700),
    ("Denim Jacket", "Fashion", 2499, 1300),
    ("Backpack", "Fashion", 1799, 900),
    ("Sunglasses", "Fashion", 1299, 550),
    ("Leather Wallet", "Fashion", 899, 400),
    ("Yoga Mat", "Fitness", 999, 450),
    ("Dumbbell Set", "Fitness", 2199, 1300),
    ("Resistance Bands", "Fitness", 599, 250),
    ("Skipping Rope", "Fitness", 299, 120),
    ("Fitness Tracker", "Fitness", 2499, 1500),
    ("Notebook Pack", "Stationery", 349, 150),
    ("Gel Pen Box", "Stationery", 199, 80),
    ("Desk Organizer", "Stationery", 649, 300),
    ("Daily Planner", "Stationery", 449, 200),
    ("Scientific Calculator", "Stationery", 899, 550),
    ("Face Wash", "Beauty", 299, 130),
    ("Sunscreen SPF50", "Beauty", 499, 230),
    ("Hair Dryer", "Beauty", 1599, 900),
    ("Perfume", "Beauty", 1999, 900),
    ("Beard Trimmer", "Beauty", 1399, 800),
]

FIRST = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Krishna", "Rohan", "Karthik", "Ishaan", "Rahul",
         "Ananya", "Diya", "Priya", "Sneha", "Kavya", "Meera", "Lakshmi", "Pooja", "Neha", "Divya"]
LAST = ["Reddy", "Sharma", "Patel", "Nair", "Iyer", "Gupta", "Singh", "Kumar", "Rao", "Naidu",
        "Menon", "Das", "Chowdary", "Verma", "Joshi"]
REGIONS = ["South", "North", "West", "East", "Central"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]


def main():
    rng = np.random.default_rng(SEED)
    out = Path(__file__).resolve().parent / "data"
    out.mkdir(exist_ok=True)

    # ---- products ----
    products = pd.DataFrame(PRODUCTS, columns=["product_name", "category", "unit_price", "unit_cost"])
    products.insert(0, "product_id", range(1, len(products) + 1))

    # ---- customers ----
    cust_ids = np.arange(1, N_CUSTOMERS + 1)
    names = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in cust_ids]
    signup = pd.to_datetime("2022-01-01") + pd.to_timedelta(rng.integers(0, 730, N_CUSTOMERS), unit="D")
    customers = pd.DataFrame({
        "customer_id": cust_ids,
        "customer_name": names,
        "region": rng.choice(REGIONS, N_CUSTOMERS, p=[0.30, 0.22, 0.20, 0.16, 0.12]),
        "segment": rng.choice(SEGMENTS, N_CUSTOMERS, p=[0.60, 0.25, 0.15]),
        "signup_date": signup.strftime("%Y-%m-%d"),
    })

    # ---- sales: seasonality (Oct-Dec peak) + growth in the last year ----
    months = pd.period_range(f"{START_YEAR}-01", f"{END_YEAR}-12", freq="M")
    seasonal = np.array([0.85, 0.80, 0.90, 0.95, 1.00, 0.95, 0.90, 0.95, 1.05, 1.20, 1.35, 1.40])
    weights = np.array([seasonal[m.month - 1] * (1.25 if m.year == END_YEAR else 1.0) for m in months])
    month_idx = rng.choice(len(months), N_ORDERS, p=weights / weights.sum())
    dates = []
    for i in month_idx:
        m = months[i]
        day = int(rng.integers(1, calendar.monthrange(m.year, m.month)[1] + 1))
        dates.append(pd.Timestamp(year=m.year, month=m.month, day=day))

    # a few customers / products are much more popular than the rest
    cw = rng.lognormal(0, 1.0, N_CUSTOMERS)
    pw = rng.lognormal(0, 0.8, len(products))
    sales = pd.DataFrame({
        "order_date": dates,
        "customer_id": rng.choice(cust_ids, N_ORDERS, p=cw / cw.sum()),
        "product_id": rng.choice(products["product_id"], N_ORDERS, p=pw / pw.sum()),
        "quantity": rng.choice([1, 2, 3, 4, 5], N_ORDERS, p=[0.50, 0.25, 0.12, 0.08, 0.05]),
        "discount": rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20], N_ORDERS),
    }).sort_values("order_date").reset_index(drop=True)
    sales.insert(0, "order_id", [f"ORD-{100001 + i}" for i in range(len(sales))])
    sales["order_date"] = sales["order_date"].dt.strftime("%Y-%m-%d")
    sales["customer_id"] = sales["customer_id"].astype("Int64")

    # ---- inject realistic data problems ----
    bad = rng.choice(len(sales), 115, replace=False)
    sales.loc[bad[:50], "customer_id"] = pd.NA                   # missing customer
    sales.loc[bad[50:90], "quantity"] = rng.choice([0, -1], 40)  # invalid quantity
    sales.loc[bad[90:], "product_id"] = 999                      # unknown product
    dupes = sales.sample(130, random_state=SEED)                 # duplicate rows
    sales = pd.concat([sales, dupes], ignore_index=True)

    products.to_csv(out / "products.csv", index=False)
    customers.to_csv(out / "customers.csv", index=False)
    sales.to_csv(out / "sales_raw.csv", index=False)
    print(f"products: {len(products)}  customers: {len(customers)}  raw sales rows: {len(sales)}")
    print(f"files written to {out}")


if __name__ == "__main__":
    main()