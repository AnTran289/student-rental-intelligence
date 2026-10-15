WITH source_count AS (
    SELECT COUNT(*) AS total
    FROM {{ ref('int_synthetic_latest_rental_listings') }}
),

aggregated_count AS (
    SELECT SUM(total_listings) AS total
    FROM {{ ref('agg_synthetic_rent_by_suburb') }}
)

SELECT
    s.total AS source_total,
    a.total AS aggregated_total
FROM source_count s
CROSS JOIN aggregated_count a
WHERE s.total <> a.total
