{{ config(materialized='view', schema='synthetic') }}

WITH source_data AS (
    SELECT *
    FROM {{ ref('synthetic_rental_listings') }}
),

cleaned AS (
    SELECT
        NULLIF(TRIM(raw_record_id), '') AS raw_record_id,
        NULLIF(TRIM(source_listing_id), '') AS source_listing_id,
        NULLIF(LOWER(TRIM(source_platform)), '') AS source_platform,
        NULLIF(TRIM(suburb), '') AS suburb,

        TRY_TO_DECIMAL(
            REPLACE(
                REPLACE(
                    REPLACE(
                        UPPER(TRIM(weekly_rent)),
                        'AUD', ''
                    ),
                    '$', ''
                ),
                ',', ''
            ),
            10, 2
        ) AS weekly_rent,

        NULLIF(LOWER(TRIM(room_type)), '') AS room_type,
        NULLIF(LOWER(TRIM(property_type)), '') AS property_type,
        NULLIF(LOWER(TRIM(furnishing_status)), '') AS furnishing_status,
        NULLIF(LOWER(TRIM(bills_status)), '') AS bills_status,
        NULLIF(LOWER(TRIM(bathroom_type)), '') AS bathroom_type,

        TRY_TO_NUMBER(bathroom_share_count)
            AS bathroom_share_count,

        TRY_TO_DATE(available_from) AS available_from,

        collected_at,
        ingested_at

    FROM source_data
)

SELECT *
FROM cleaned