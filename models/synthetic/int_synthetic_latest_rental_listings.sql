{{ config(materialized='view', schema='synthetic') }}

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY source_platform, source_listing_id
            ORDER BY collected_at DESC NULLS LAST,
                     ingested_at DESC NULLS LAST,
                     raw_record_id DESC NULLS LAST
        ) AS row_num
    FROM {{ ref('int_synthetic_valid_rental_listings') }}
)

SELECT * EXCLUDE (row_num)
FROM ranked
WHERE row_num = 1
