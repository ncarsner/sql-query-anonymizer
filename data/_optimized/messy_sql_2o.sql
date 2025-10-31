SELECT
  c.customer_id, c.first_name, c.last_name, c.email, c.phone,
  c.address, c.city, c.state, c.zip_code,
  o.order_id, o.order_date, o.total_amount, o.status,
  CASE
    WHEN o.total_amount > 1000 THEN 'High Value'
    WHEN o.total_amount >  500 THEN 'Medium Value'
    ELSE 'Low Value'
  END AS order_category,
  COUNT(o.order_id)   OVER (PARTITION BY c.customer_id) AS total_orders,
  AVG(o.total_amount) OVER (PARTITION BY c.customer_id) AS avg_order_amount
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id
WHERE c.created_date >= '2023-01-01'
  AND c.state IN ('CA','NY','TX','FL')
  AND NULLIF(TRIM(c.email), '') IS NOT NULL
ORDER BY c.last_name, c.first_name, o.order_date DESC;
