SELECT
  c.*,
  o.order_count,
  o.max_order
FROM table_2 AS c
LEFT JOIN (
  SELECT
    identifier_1,
    COUNT(*)        AS order_count,
    MAX(identifier_3) AS max_order
  FROM table_1
  GROUP BY identifier_1
) AS o
  ON o.identifier_1 = c.identifier_2
WHERE
  c.identifier_4 = literal_1
  AND c.identifier_5 > literal_2
  -- replaces: c.identifier_2 IN (SELECT DISTINCT identifier_1 FROM table_1 WHERE identifier_6 >= literal_3)
  AND EXISTS (
    SELECT 1
    FROM table_1 t1
    WHERE t1.identifier_1 = c.identifier_2
      AND t1.identifier_6 >= literal_3
  )
  AND EXISTS (
    SELECT 1
    FROM table_3 cp
    WHERE cp.identifier_1 = c.identifier_2
      AND cp.identifier_7 = literal_5
  )
ORDER BY c.identifier_8, c.identifier_9
LIMIT literal_6;
