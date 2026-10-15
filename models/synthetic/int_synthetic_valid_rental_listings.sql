{{ config(materialized='view', schema='synthetic') }}

WITH validated AS (
    SELECT
        *,
        CASE
            WHEN NULLIF(TRIM(raw_record_id), '') IS NULL THEN 'REJECTED'
            WHEN NULLIF(TRIM(source_platform), '') IS NULL THEN 'REJECTED'
            WHEN NULLIF(TRIM(source_listing_id), '') IS NULL THEN 'REJECTED'
            WHEN NULLIF(TRIM(suburb), '') IS NULL THEN 'REJECTED'
            WHEN weekly_rent IS NULL THEN 'REJECTED'
            WHEN weekly_rent <= 0 THEN 'REJECTED'
            WHEN collected_at IS NULL THEN 'REJECTED'
            ELSE 'VALID'
        END AS dq_status
    FROM {{ ref('stg_synthetic_rental_listings') }}
)

SELECT *
FROM validated
WHERE dq_status = 'VALID'