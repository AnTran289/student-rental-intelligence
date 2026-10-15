SELECT
    suburb,
    room_type,
    COUNT(*) AS duplicate_count
FROM {{ ref('agg_synthetic_rent_by_suburb_room_type') }}
GROUP BY suburb, room_type 
HAVING COUNT(*) > 1
