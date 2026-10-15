SELECT *
FROM {{ ref('agg_synthetic_rent_distribution') }}
WHERE
    total_listings <= 0
    OR avg_weekly_rent IS NULL
    OR CASE
        WHEN price_band = 'Under $250'
            THEN avg_weekly_rent >= 250
        WHEN price_band = '$250-299'
            THEN avg_weekly_rent < 250
              OR avg_weekly_rent >= 300
        WHEN price_band = '$300-349'
            THEN avg_weekly_rent < 300
              OR avg_weekly_rent >= 350
        WHEN price_band = '$350+'
            THEN avg_weekly_rent < 350
        ELSE TRUE
    END