
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
                ingested_at DESC NULLS LAST,
                raw_record_id DESC
        ) AS row_num

    FROM valid_listings
)

SELECT *
EXCLUDE (row_num)
FROM ranked_listings
WHERE row_num = 1
