SELECT c.customer_id, c.first_name, c.last_name, c.email, c.phone, c.address, c.city, c.state, c.zip_code,
    o.order_id, o.order_date, o.total_amount, o.status,
    CASE 
      WHEN o.total_amount > 1000 THEN 'High Value'
      WHEN o.total_amount > 500 THEN 'Medium Value'
      ELSE 'Low Value'
    END as order_category,
    (SELECT COUNT(*) FROM orders o2 WHERE o2.customer_id = c.customer_id) as total_orders,
    (SELECT AVG(total_amount) FROM orders o3 WHERE o3.customer_id = c.customer_id) as avg_order_amount 
FROM customers c 
LEFT JOIN orders o ON c.customer_id = o.customer_id 
WHERE c.created_date >= '2023-01-01'
  AND (c.state = 'CA' OR c.state = 'NY' OR c.state = 'TX' OR c.state = 'FL')
  AND c.email IS NOT NULL
  AND c.email != '' 
ORDER BY c.last_name, c.first_name, o.order_date DESC;

-- This query retrieves customer details along with their orders placed since January 1, 2023.
-- It categorizes orders based on their total amount and calculates total and average order amounts per customer.
-- The results are filtered to include only customers from specific states with valid email addresses.
-- Note: Ensure indexes exist on customers.customer_id, orders.customer_id, and customers.state for optimal performance.
