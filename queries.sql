-- All SQL for the project. Each query starts with a "-- name:" line,
-- and the Python code uses that name to find it.

-- name: clean_sales
INSERT INTO sales (order_id, order_date, customer_id, product_id, quantity, discount, revenue, profit)
SELECT r.order_id,
       r.order_date,
       r.customer_id,
       r.product_id,
       r.quantity,
       COALESCE(r.discount, 0),
       ROUND(r.quantity * p.unit_price * (1 - COALESCE(r.discount, 0)), 2),
       ROUND(r.quantity * p.unit_price * (1 - COALESCE(r.discount, 0)) - r.quantity * p.unit_cost, 2)
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_date) AS rn
    FROM sales_raw
    WHERE order_id IS NOT NULL
) AS r
JOIN products  AS p ON p.product_id  = r.product_id
JOIN customers AS c ON c.customer_id = r.customer_id
WHERE r.rn = 1
  AND r.quantity > 0
  AND r.order_date IS NOT NULL;

-- name: data_quality
SELECT
    (SELECT COUNT(*) FROM sales_raw)                                  AS raw_rows,
    (SELECT COUNT(*) FROM sales)                                      AS clean_rows,
    (SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM sales_raw)       AS duplicate_rows,
    (SELECT COUNT(*) FROM sales_raw WHERE customer_id IS NULL)        AS missing_customer,
    (SELECT COUNT(*) FROM sales_raw WHERE quantity <= 0)              AS invalid_quantity,
    (SELECT COUNT(*) FROM sales_raw
      WHERE product_id NOT IN (SELECT product_id FROM products))      AS unknown_product;

-- name: raw_vs_clean_revenue
SELECT
    (SELECT ROUND(SUM(r.quantity * p.unit_price * (1 - COALESCE(r.discount, 0))), 2)
       FROM sales_raw r JOIN products p ON p.product_id = r.product_id) AS raw_revenue,
    (SELECT ROUND(SUM(revenue), 2) FROM sales)                          AS clean_revenue;

-- name: monthly_sales
WITH m AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           COUNT(*)                      AS orders,
           SUM(quantity)                 AS units,
           SUM(revenue)                  AS revenue,
           SUM(profit)                   AS profit
    FROM sales
    GROUP BY 1
)
SELECT month,
       orders,
       units,
       ROUND(revenue, 2)                                  AS revenue,
       ROUND(profit, 2)                                   AS profit,
       ROUND(revenue * 1.0 / orders, 2)                   AS avg_order_value,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                   / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM m
ORDER BY month;

-- name: yearly_sales
WITH y AS (
    SELECT strftime('%Y', order_date) AS year,
           COUNT(*)                   AS orders,
           SUM(quantity)              AS units,
           SUM(revenue)               AS revenue,
           SUM(profit)                AS profit
    FROM sales
    GROUP BY 1
)
SELECT year,
       orders,
       units,
       ROUND(revenue, 2)                                  AS revenue,
       ROUND(profit, 2)                                   AS profit,
       ROUND(100.0 * profit / revenue, 1)                 AS margin_pct,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
                   / LAG(revenue) OVER (ORDER BY year), 1) AS yoy_growth_pct
FROM y
ORDER BY year;

-- name: top_products
SELECT p.product_name,
       p.category,
       SUM(s.quantity)                                    AS units_sold,
       ROUND(SUM(s.revenue), 2)                           AS revenue,
       ROUND(SUM(s.profit), 2)                            AS profit,
       RANK() OVER (ORDER BY SUM(s.revenue) DESC)         AS revenue_rank
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 10;

-- name: category_sales
SELECT p.category,
       COUNT(*)                                           AS orders,
       ROUND(SUM(s.revenue), 2)                           AS revenue,
       ROUND(SUM(s.profit), 2)                            AS profit,
       ROUND(100.0 * SUM(s.profit) / SUM(s.revenue), 1)   AS margin_pct
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- name: region_sales
SELECT c.region,
       COUNT(DISTINCT c.customer_id)                      AS customers,
       COUNT(*)                                           AS orders,
       ROUND(SUM(s.revenue), 2)                           AS revenue,
       ROUND(100.0 * SUM(s.revenue) / (SELECT SUM(revenue) FROM sales), 1) AS revenue_share_pct
FROM sales AS s
JOIN customers AS c ON c.customer_id = s.customer_id
GROUP BY c.region
ORDER BY revenue DESC;

-- name: top_customers
SELECT c.customer_id,
       c.customer_name,
       c.region,
       c.segment,
       COUNT(*)                                           AS orders,
       ROUND(SUM(s.revenue), 2)                           AS revenue,
       MIN(s.order_date)                                  AS first_order,
       MAX(s.order_date)                                  AS last_order
FROM sales AS s
JOIN customers AS c ON c.customer_id = s.customer_id
GROUP BY c.customer_id
ORDER BY revenue DESC
LIMIT 10;

-- name: customer_types
WITH per_customer AS (
    SELECT customer_id, COUNT(*) AS orders, SUM(revenue) AS revenue
    FROM sales
    GROUP BY customer_id
)
SELECT CASE WHEN orders >= 25 THEN '1. Loyal (25+ orders)'
            WHEN orders >= 10 THEN '2. Regular (10-24 orders)'
            ELSE                   '3. Occasional (1-9 orders)' END AS customer_type,
       COUNT(*)                                           AS customers,
       ROUND(SUM(revenue), 2)                             AS revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM sales), 1) AS revenue_share_pct
FROM per_customer
GROUP BY 1
ORDER BY 1;