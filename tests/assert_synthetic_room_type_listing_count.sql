WITH source_count AS (
    SELECT COUNT(*) AS total
    FROM {{ ref('int_synthetic_latest_rental_listings') }}
),

mart_count AS (
    SELECT SUM(total_listings) AS total
    FROM {{ ref('agg_synthetic_rent_by_suburb_room_type') }}
)

SELECT
    s.total AS source_total,
    m.total AS mart_total
FROM source_count s
CROSS JOIN mart_count m
WHERE s.total <> m.total