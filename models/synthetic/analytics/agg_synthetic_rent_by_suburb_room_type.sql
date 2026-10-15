{{ config(
    materialized='table',
    schema='synthetic'
) }}

WITH rental_listings AS (
    SELECT
        suburb,
        room_type,
        weekly_rent
    FROM {{ ref('int_synthetic_latest_rental_listings') }}
),

aggregated AS (
    SELECT
        suburb,
        room_type,
        COUNT(*) AS total_listings,
        ROUND(AVG(weekly_rent), 2) AS avg_weekly_rent,
        MEDIAN(weekly_rent) AS median_weekly_rent,
        MIN(weekly_rent) AS min_weekly_rent,
        MAX(weekly_rent) AS max_weekly_rent
    FROM rental_listings
    GROUP BY suburb, room_type
)

SELECT *
FROM aggregated