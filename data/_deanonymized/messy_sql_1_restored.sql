SELECT
    c.*,
    o.order_count,
    o.max_order
FROM
    customers AS c
    LEFT JOIN (
        SELECT
            customer_id,
            COUNT(*) AS order_count,
            MAX(total_amount) AS max_order
        FROM
            orders
        GROUP BY
            customer_id
    ) AS o ON o.customer_id = c.id
WHERE
    c.status = 'active'
    AND c.created_date > '2020-01-01'
    AND EXISTS (
        SELECT
            1
        FROM
            orders t1
        WHERE
            t1.customer_id = c.id
            AND t1.order_date >= '2023-01-01'
    )
    AND EXISTS (
        SELECT
            1
        FROM
            customer_preferences cp
        WHERE
            cp.customer_id = c.id
            AND cp.email_marketing = 'yes'
    )
ORDER BY
    c.last_name,
    c.first_name
LIMIT
    1000;