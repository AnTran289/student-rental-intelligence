WITH latest_listings AS (
    SELECT *
    FROM {{ ref('int_latest_rental_listings') }}
),

final AS (
    SELECT
        MD5(
            source_platform || '|' || source_listing_id
        ) AS listing_key,

        MD5(suburb) AS suburb_key,

        raw_record_id,
        source_platform,
        source_listing_id,

        weekly_rent,
        room_type,
        property_type,
        furnishing_status,
        bills_status,
        bathroom_type,
        bathroom_share_count,

        available_from,
        collected_at,
        ingested_at

    FROM latest_listings
)

SELECT *
FROM final
