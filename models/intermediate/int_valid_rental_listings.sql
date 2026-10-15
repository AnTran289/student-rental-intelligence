SELECT *
FROM {{ ref('stg_rental_listings') }}
WHERE dq_status = 'VALID'
