SELECT
    *,
    (
        SELECT
            COUNT(*)
        FROM
            table_1 o2
        WHERE
            o2.identifier_1 = c.identifier_2
    ) AS order_count,
    (
        SELECT
            MAX(identifier_3)
        FROM
            table_1 o3
        WHERE
            o3.identifier_1 = c.identifier_2
    ) AS max_order
FROM
    table_2 c
WHERE
    c.identifier_4 = literal_1
    AND c.identifier_5 > literal_2
    AND c.identifier_2 IN (
        SELECT DISTINCT
            identifier_1
        FROM
            table_1
        WHERE
            identifier_6 >= literal_3
    )
    AND EXISTS (
        SELECT
            literal_4
        FROM
            table_3 cp
        WHERE
            cp.identifier_1 = c.identifier_2
            AND cp.identifier_7 = literal_5
    )
ORDER BY
    c.identifier_8,
    c.identifier_9
LIMIT
    literal_6;