SELECT
    listing_key,
    weekly_rent
FROM {{ ref('fct_rental_listings') }}
WHERE weekly_rent <= 0
