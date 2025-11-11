SELECT
    c.identifier_1,
    c.identifier_2,
    c.identifier_3,
    c.identifier_4,
    c.identifier_5,
    c.identifier_6,
    c.identifier_7,
    c.identifier_8,
    c.identifier_9,
    o.identifier_10,
    o.identifier_11,
    o.identifier_12,
    o.identifier_13,
    CASE
        WHEN o.identifier_12 > literal_1 THEN literal_2
        WHEN o.identifier_12 > literal_3 THEN literal_4
        ELSE literal_5
    END AS order_category,
    (
        SELECT
            COUNT(*)
        FROM
            table_1 o2
        WHERE
            o2.identifier_1 = c.identifier_1
    ) AS total_orders,
    (
        SELECT
            AVG(identifier_12)
        FROM
            table_1 o3
        WHERE
            o3.identifier_1 = c.identifier_1
    ) AS avg_order_amount
FROM
    table_2 c
    LEFT JOIN table_1 o ON c.identifier_1 = o.identifier_1
WHERE
    c.identifier_14 >= literal_6
    AND (
        c.identifier_8 = literal_7
        OR c.identifier_8 = literal_8
        OR c.identifier_8 = literal_9
        OR c.identifier_8 = literal_10
    )
    AND c.identifier_4 IS NOT NULL
    AND c.identifier_4 != literal_11
ORDER BY
    c.identifier_3,
    c.identifier_2,
    o.identifier_11 identifier_15;