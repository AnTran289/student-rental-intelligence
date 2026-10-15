SELECT
    source_platform,
    source_listing_id,
    COUNT(*) AS duplicate_count
FROM {{ ref('int_latest_rental_listings') }}
GROUP BY
    source_platform,
    source_listing_id
HAVING COUNT(*) > 1
