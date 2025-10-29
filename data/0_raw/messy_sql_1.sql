SELECT *,
    (SELECT COUNT(*) FROM orders o2 WHERE o2.customer_id = customers.id) as order_count,
    (SELECT MAX(total_amount) FROM orders o3 WHERE o3.customer_id = customers.id) as max_order
FROM customers
WHERE customers.status = 'active'
   AND customers.created_date > '2020-01-01'
   AND customers.id IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE order_date >= '2023-01-01'
   )
   AND EXISTS (
    SELECT 'X'
    FROM customer_preferences cp 
    WHERE cp.customer_id = customers.id 
      AND cp.email_marketing = 'yes'
   )
ORDER BY customers.last_name, customers.first_name
LIMIT 1000;
-- This query retrieves active customers created after January 1, 2020,
-- along with their order counts and maximum order amounts from 2023 onwards.
-- It also filters customers based on their email marketing preferences.
-- Note: Ensure that appropriate indexes exist on customers.id, orders.customer_id, and customer_preferences.customer_id for optimal performance.
