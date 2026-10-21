from ingestion.snowflake_connection import get_snowflake_connection
from ingestion.snowflake_loader import load_rental_batch

record = {
    "RAW_RECORD_ID": "INT_TEST_001",
    "SOURCE_LISTING_ID": "INT_SYN_001",
    "SOURCE_PLATFORM": "SYNTHETIC",
    "SUBURB": "Figtree",
    "WEEKLY_RENT": "$290",
    "ROOM_TYPE": "private",
    "PROPERTY_TYPE": "house",
    "FURNISHING_STATUS": "fully_furnished",
    "BILLS_STATUS": "equally_divided",
    "BATHROOM_TYPE": None,
    "BATHROOM_SHARE_COUNT": "3",
    "AVAILABLE_FROM": "2026-11-01",
    "COLLECTED_AT": "2026-10-20 10:00:00",
}

# def main():
#     connection = get_snowflake_connection()

#     try:
#         result = load_rental_batch(connection, [record])
#         print("Batch result:", result)
#     finally:
#         connection.close()


# if __name__ == "__main__":
#     main()


def main():
    connection = get_snowflake_connection()

    try:
        conflicting_record = record.copy()
        conflicting_record["WEEKLY_RENT"] = "$350"

        try:
            load_rental_batch(connection, [conflicting_record])
            print("UNEXPECTED: Conflict was not detected")

        except ValueError as error:
            print("EXPECTED CONFLICT:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

