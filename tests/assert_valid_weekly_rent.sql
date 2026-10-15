SELECT
    raw_record_id,
    weekly_rent
FROM {{ ref('int_valid_rental_listings') }}
WHERE weekly_rent <= 0