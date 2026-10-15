SELECT
    price_band,
    room_type,
    COUNT(*) AS duplicate_count
FROM {{ ref('agg_synthetic_rent_distribution') }}
GROUP BY price_band, room_type
HAVING COUNT(*) > 1