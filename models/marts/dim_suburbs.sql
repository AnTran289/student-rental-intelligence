WITH unique_suburbs AS (
    SELECT DISTINCT
        suburb
    FROM {{ ref('int_latest_rental_listings') }}
    WHERE suburb IS NOT NULL
),

final AS (
    SELECT
        MD5(suburb) AS suburb_key,
        suburb AS suburb_name
    FROM unique_suburbs
)

SELECT *
FROM final
