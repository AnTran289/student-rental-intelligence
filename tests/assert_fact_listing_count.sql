WITH intermediate_count AS (
    SELECT COUNT(*) AS total
    FROM {{ ref('int_latest_rental_listings') }}
),

fact_count AS (
    SELECT COUNT(*) AS total
    FROM {{ ref('fct_rental_listings') }}
)

SELECT
    i.total AS intermediate_total,
    f.total AS fact_total
FROM intermediate_count i
CROSS JOIN fact_count f
WHERE i.total <> f.total
