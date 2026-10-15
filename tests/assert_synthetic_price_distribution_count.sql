WITH source_count AS (
    SELECT COUNT(*) AS total
    FROM {{ ref('int_synthetic_latest_rental_listings') }}
    WHERE weekly_rent IS NOT NULL
      AND weekly_rent > 0
),

mart_count AS (
    SELECT COALESCE(SUM(total_listings), 0) AS total
    FROM {{ ref('agg_synthetic_rent_distribution') }}
)

SELECT
    s.total AS source_total,
    m.total AS mart_total
FROM source_count s
CROSS JOIN mart_count m
WHERE s.total <> m.total