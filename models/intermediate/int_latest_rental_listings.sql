
WITH valid_listings AS (
    SELECT *
    FROM {{ ref('int_valid_rental_listings') }}
),

ranked_listings AS (
    SELECT
        *,

        ROW_NUMBER() OVER (
            PARTITION BY
                source_platform,
                source_listing_id
            ORDER BY
                collected_at DESC NULLS LAST,
                raw_record_id DESC
        ) AS row_num

    FROM valid_listings
)

SELECT
-- *
-- EXCLUDE (row_num)
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
    collected_at,
    available_from,
    ingested_at,
    dq_status,
    dq_reason
FROM ranked_listings
WHERE row_num = 1
