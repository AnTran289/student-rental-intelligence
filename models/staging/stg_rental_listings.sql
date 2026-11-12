WITH source_data AS (
    SELECT *
    FROM {{ source('raw', 'rental_listings') }}
),

normalized AS (
    SELECT
        raw_record_id,
        NULLIF(TRIM(source_listing_id), '')
            AS source_listing_id,
        NULLIF(LOWER(TRIM(source_platform)), '')
            AS source_platform,

        INITCAP(TRIM(suburb)) AS suburb,

        -- TRY_TO_DECIMAL(
        --     REGEXP_REPLACE(weekly_rent, '[^0-9.-]', ''),
        --     10, 2
        -- ) AS weekly_rent,

        REGEXP_REPLACE(
            weekly_rent, '[^0-9.-]', '', 'g'
        ) AS cleaned_rent,

        LOWER(TRIM(room_type)) AS room_type,
        LOWER(TRIM(property_type)) AS property_type,
        LOWER(TRIM(furnishing_status)) AS furnishing_status,
        LOWER(TRIM(bills_status)) AS bills_status,
        LOWER(TRIM(bathroom_type)) AS bathroom_type,

        -- TRY_TO_NUMBER(bathroom_share_count)
        --     AS bathroom_share_count,

        NULLIF(TRIM(bathroom_share_count), '')
            AS raw_bathroom_share_count,

        collected_at,
        available_from,
        ingested_at

    FROM source_data
),

cleaned AS (
    SELECT
        normalized.*,

        CASE
            WHEN cleaned_rent ~ '^-?[0-9]+(\.[0-9]{1,2})?$'
                 AND LENGTH(
                     SPLIT_PART(
                         LTRIM(cleaned_rent, '-'),
                         '.',
                         1
                     )
                 ) <= 8
            THEN cleaned_rent::NUMERIC(10,2)
            ELSE NULL
        END AS weekly_rent,

        CASE
            WHEN raw_bathroom_share_count ~ '^[0-9]+$'
                 AND LENGTH(raw_bathroom_share_count) <= 9
            THEN raw_bathroom_share_count::INT
            ELSE NULL
        END AS bathroom_share_count

    FROM normalized
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
    collected_at,
    available_from,
    ingested_at,
    dq_status,
    dq_reason
FROM classified
