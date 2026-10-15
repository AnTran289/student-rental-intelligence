{{ config(
    materialized='table',
    schema='synthetic'
) }}

WITH classified_listings AS (
    SELECT
        raw_record_id,
        room_type,
        weekly_rent,

        CASE
            WHEN weekly_rent < 250 THEN 'Under $250'
            WHEN weekly_rent < 300 THEN '$250-299'
            WHEN weekly_rent < 350 THEN '$300-349'
            ELSE '$350+'
        END AS price_band,

        CASE
            WHEN weekly_rent < 250 THEN 1
            WHEN weekly_rent < 300 THEN 2
            WHEN weekly_rent < 350 THEN 3
            ELSE 4
        END AS price_band_order

    FROM {{ ref('int_synthetic_latest_rental_listings') }}
    WHERE weekly_rent IS NOT NULL
      AND weekly_rent > 0
),

aggregated AS (
    SELECT
        price_band,
        price_band_order,
        room_type,
        COUNT(*) AS total_listings,
        ROUND(AVG(weekly_rent), 2) AS avg_weekly_rent
    FROM classified_listings
    GROUP BY
        price_band,
        price_band_order,
        room_type
)

SELECT *
FROM aggregated