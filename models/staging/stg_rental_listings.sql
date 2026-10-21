WITH source_data AS (
    SELECT *
    FROM {{ source('raw', 'rental_listings') }}
),

cleaned AS (
    SELECT
        raw_record_id,
        NULLIF(TRIM(source_listing_id), '')
            AS source_listing_id,
        NULLIF(LOWER(TRIM(source_platform)), '')
            AS source_platform,

        INITCAP(TRIM(suburb)) AS suburb,

        TRY_TO_DECIMAL(
            REGEXP_REPLACE(weekly_rent, '[^0-9.-]', ''),
            10, 2
        ) AS weekly_rent,

        LOWER(TRIM(room_type)) AS room_type,
        LOWER(TRIM(property_type)) AS property_type,
        LOWER(TRIM(furnishing_status)) AS furnishing_status,
        LOWER(TRIM(bills_status)) AS bills_status,
        LOWER(TRIM(bathroom_type)) AS bathroom_type,

        TRY_TO_NUMBER(bathroom_share_count)
            AS bathroom_share_count,
        
        collected_at,
        available_from,
        ingested_at

    FROM source_data
),


classified AS (
    SELECT
        *,

        CASE
            WHEN source_platform IS NULL
                THEN 'REJECTED'
            WHEN source_listing_id IS NULL
                THEN 'REJECTED'
            WHEN raw_record_id IS NULL
                THEN 'REJECTED'
            WHEN suburb IS NULL OR suburb = ''
                THEN 'REJECTED'
            WHEN weekly_rent IS NULL
                THEN 'REJECTED'
            WHEN weekly_rent <= 0
                THEN 'REJECTED'
            ELSE 'VALID'
        END AS dq_status,

        CASE
            WHEN source_platform IS NULL
                THEN 'MISSING_SOURCE_PLATFORM'
            WHEN source_listing_id IS NULL
                THEN 'MISSING_SOURCE_LISTING_ID'
            WHEN raw_record_id IS NULL
                THEN 'MISSING_RECORD_ID'
            WHEN suburb IS NULL OR suburb = ''
                THEN 'MISSING_SUBURB'
            WHEN weekly_rent IS NULL
                THEN 'MISSING_OR_INVALID_RENT'
            WHEN weekly_rent <= 0
                THEN 'NON_POSITIVE_RENT'
            ELSE NULL
        END AS dq_reason

    FROM cleaned
)

SELECT *
FROM classified
