{{ config(materialized='view', schema='synthetic') }}

-- WITH ranked AS (
--     SELECT
--         *,
--         ROW_NUMBER() OVER (
--             PARTITION BY source_platform, source_listing_id
--             ORDER BY collected_at DESC NULLS LAST,
--                      ingested_at DESC NULLS LAST,
--                      raw_record_id DESC NULLS LAST
--         ) AS row_num
--     FROM {{ ref('int_synthetic_valid_rental_listings') }}
-- )

-- SELECT * EXCLUDE (row_num)
-- FROM ranked
-- WHERE row_num = 1

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY source_platform, source_listing_id
            ORDER BY
                collected_at DESC NULLS LAST,
                raw_record_id DESC
        ) AS row_num
    FROM {{ ref('int_synthetic_valid_rental_listings') }}
)

SELECT
    raw_record_id,
    source_listing_id,
    source_platform,
    suburb,
    weekly_rent,
    room_type,
    property_type,
    furnishing_status,
    bills_status,
    bathroom_type,
    bathroom_share_count,
    available_from,
    collected_at,
    ingested_at,
    dq_status
FROM ranked
WHERE row_num = 1
