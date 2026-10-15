{{ config(
    materialized='table',
    schema='synthetic'
) }}

WITH suburb_aggregations AS (
    SELECT
        suburb,
        COUNT(*) AS total_listings,
        ROUND(AVG(weekly_rent), 2) AS avg_weekly_rent,
        MEDIAN(weekly_rent) AS median_weekly_rent,
        MIN(weekly_rent) AS min_weekly_rent,
        MAX(weekly_rent) AS max_weekly_rent

    FROM {{ ref('int_synthetic_latest_rental_listings') }}

    GROUP BY suburb
)

SELECT
    suburb,
    total_listings,
    avg_weekly_rent,
    median_weekly_rent,
    min_weekly_rent,
    max_weekly_rent

FROM suburb_aggregations
