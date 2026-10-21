SELECT *
FROM {{ ref('_listings') }}
WHERE dq_status = 'REJECTED'