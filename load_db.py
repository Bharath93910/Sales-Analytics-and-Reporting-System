import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = BASE / "sales.db"


def load_queries(path):
    """Split queries.sql into {name: sql} using the '-- name:' marker lines."""
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


queries = load_queries(BASE / "queries.sql")

if DB.exists():
    DB.unlink()  # start fresh every time

conn = sqlite3.connect(DB)
conn.executescript((BASE / "schema.sql").read_text(encoding="utf-8"))

pd.read_csv(DATA / "customers.csv").to_sql("customers", conn, if_exists="append", index=False)
pd.read_csv(DATA / "products.csv").to_sql("products", conn, if_exists="append", index=False)
raw = pd.read_csv(DATA / "sales_raw.csv", dtype={"customer_id": "Int64"})
raw.to_sql("sales_raw", conn, if_exists="append", index=False)

conn.execute(queries["clean_sales"])  # the cleaning step
conn.commit()

REPORT_DIR = BASE / "reports"
REPORT_DIR.mkdir(exist_ok=True)

for name in ("monthly_sales", "yearly_sales", "top_products", "category_sales", "region_sales", "top_customers", "customer_types"):
    df = pd.read_sql_query(queries[name], conn)
    df.to_csv(REPORT_DIR / f"{name}.csv", index=False)  # saves the report as a CSV file
    print(f"\n{name}")
    print(df.to_string(index=False))

conn.close()