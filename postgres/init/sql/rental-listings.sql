CREATE SCHEMA raw;

CREATE TABLE raw.rental_listings (
    raw_record_id varchar(50) PRIMARY KEY,
    source_listing_id varchar(100),
    source_platform varchar(100),
    suburb varchar(100),
    weekly_rent varchar(50),
    room_type varchar(50),
    property_type varchar(50),
    furnishing_status varchar(50),
    bills_status varchar(50),
    bathroom_type varchar(50),
    bathroom_share_count varchar(20),
    available_from varchar(100),
    ingested_at timestamp(6) without time zone DEFAULT LOCALTIMESTAMP,
    collected_at timestamp(6) without time zone
);
