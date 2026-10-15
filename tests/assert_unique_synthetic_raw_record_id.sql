SELECT
    raw_record_id,
    COUNT(*) AS duplicate_count
FROM {{ ref('stg_synthetic_rental_listings') }}
GROUP BY raw_record_id
HAVING COUNT(*) > 1