{{ config(materialized='view', schema='synthetic') }}

WITH source_data AS (
    SELECT *
    FROM {{ ref('synthetic_rental_listings') }}
),

normalized AS (
    SELECT
        *,

        -- Normalize weekly_rent
        REGEXP_REPLACE(
            weekly_rent,
            '[^0-9.-]',
            '',
            'g'
        ) AS cleaned_rent,

        -- Normalize bathroom_share_count
        NULLIF(
            TRIM(bathroom_share_count),
            ''
        ) AS cleaned_bathroom_share_count,

        -- Normalize available_from
        NULLIF(
            TRIM(available_from),
            ''
        ) AS date_string

    FROM source_data
),

typed_values AS (
    SELECT
        *,

        -- Safe NUMERIC conversion
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
        END AS parsed_rent,

        -- Safe INTEGER conversion
        CASE
            WHEN cleaned_bathroom_share_count ~ '^[0-9]+$'
                AND LENGTH(cleaned_bathroom_share_count) <= 9
            THEN cleaned_bathroom_share_count::INTEGER
            ELSE NULL
        END AS parsed_bathroom_share_count

    FROM normalized
),

date_parts AS (
    SELECT
        *,
        CASE
            WHEN date_string ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            THEN SUBSTRING(date_string, 1, 4)::INT
        END AS year_num,

        CASE
            WHEN date_string ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            THEN SUBSTRING(date_string, 6, 2)::INT
        END AS month_num,

        CASE
            WHEN date_string ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            THEN SUBSTRING(date_string, 9, 2)::INT
        END AS day_num
    FROM typed_values
),

validated_parts AS (
    SELECT
        *,
        CASE
            WHEN year_num BETWEEN 1 AND 9999
             AND month_num BETWEEN 1 AND 12
             AND day_num BETWEEN 1 AND 31
            THEN 'VALID_RANGE'
            ELSE 'INVALID_RANGE'
        END AS range_status
    FROM date_parts
),

calendar_check AS (
    SELECT
        *,
        CASE
            WHEN range_status = 'VALID_RANGE'
            THEN EXTRACT(
                DAY FROM (
                    MAKE_DATE(year_num, month_num, 1)
                    + INTERVAL '1 month'
                    - INTERVAL '1 day'
                )
            )::INT
        END AS days_in_month
    FROM validated_parts
),

cleaned AS (
    SELECT
        NULLIF(TRIM(raw_record_id), '') AS raw_record_id,
        NULLIF(TRIM(source_listing_id), '') AS source_listing_id,
        NULLIF(LOWER(TRIM(source_platform)), '') AS source_platform,
        NULLIF(TRIM(suburb), '') AS suburb,

        -- TRY_TO_DECIMAL(
        --     REPLACE(
        --         REPLACE(
        --             REPLACE(
        --                 UPPER(TRIM(weekly_rent)),
        --                 'AUD', ''
        --             ),
        --             '$', ''
        --         ),
        --         ',', ''
        --     ),
        --     10, 2
        -- ) AS weekly_rent,

        parsed_rent AS weekly_rent,

        NULLIF(LOWER(TRIM(room_type)), '') AS room_type,
        NULLIF(LOWER(TRIM(property_type)), '') AS property_type,
        NULLIF(LOWER(TRIM(furnishing_status)), '') AS furnishing_status,
        NULLIF(LOWER(TRIM(bills_status)), '') AS bills_status,
        NULLIF(LOWER(TRIM(bathroom_type)), '') AS bathroom_type,

        -- TRY_TO_NUMBER(bathroom_share_count)
        --     AS bathroom_share_count,

        parsed_bathroom_share_count AS bathroom_share_count,

        -- TRY_TO_DATE(available_from) AS available_from,
        CASE
            WHEN day_num BETWEEN 1 AND days_in_month
            THEN MAKE_DATE(year_num, month_num, day_num)
            ELSE NULL
        END AS available_from,

        collected_at,
        ingested_at

    FROM calendar_check
)

SELECT *
FROM cleaned