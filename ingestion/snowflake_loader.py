def merge_rental_record(connection, record):
    # """
    # Insert a rental observation if RAW_RECORD_ID does not exist.
    # """

    # sql = """
    # MERGE INTO STUDENT_RENTAL_DB.RAW.RENTAL_LISTINGS AS target

    # USING (
    #     SELECT
    #         %s AS RAW_RECORD_ID,
    #         %s AS SOURCE_LISTING_ID,
    #         %s AS WEEKLY_RENT,
    #         TRY_TO_TIMESTAMP_NTZ(%s) AS COLLECTED_AT
    # ) AS source

    # ON target.RAW_RECORD_ID = source.RAW_RECORD_ID

    # WHEN NOT MATCHED THEN
    #     INSERT (
    #         RAW_RECORD_ID,
    #         SOURCE_LISTING_ID,
    #         WEEKLY_RENT,
    #         COLLECTED_AT
    #     )
    #     VALUES (
    #         source.RAW_RECORD_ID,
    #         source.SOURCE_LISTING_ID,
    #         source.WEEKLY_RENT,
    #         source.COLLECTED_AT
    #     )
    # """

    # cursor = connection.cursor()

    """
    Execute an insert-only MERGE for one rental observation.

    Transaction commit/rollback is handled by the caller.
    """

    # Build SQL and parameters
    sql = build_merge_sql()
    params = build_record_params(record)

    # Create cursor
    cursor = connection.cursor()

    try:
        cursor.execute(
            sql,
            params
        )
    finally:
        cursor.close()

# Define the expected columns in the RAW.RENTAL_LISTINGS table
RAW_COLUMNS = [
    "RAW_RECORD_ID",
    "SOURCE_LISTING_ID",
    "SOURCE_PLATFORM",
    "SUBURB",
    "WEEKLY_RENT",
    "ROOM_TYPE",
    "PROPERTY_TYPE",
    "FURNISHING_STATUS",
    "BILLS_STATUS",
    "BATHROOM_TYPE",
    "BATHROOM_SHARE_COUNT",
    "AVAILABLE_FROM",
    "COLLECTED_AT",
]

def build_record_params(record):
    """
    Return a tuple of values matching RAW_COLUMNS order.
    """
    # return (
    #     record["RAW_RECORD_ID"],
    #     record.get("SOURCE_LISTING_ID"),
    #     record.get("SOURCE_PLATFORM"),
    #     record.get("SUBURB"),
    #     record.get("WEEKLY_RENT"),
    #     record.get("ROOM_TYPE"),
    #     record.get("PROPERTY_TYPE"),
    #     record.get("FURNISHING_STATUS"),
    #     record.get("BILLS_STATUS"),
    #     record.get("BATHROOM_TYPE"),
    #     record.get("BATHROOM_SHARE_COUNT"),
    #     record.get("AVAILABLE_FROM"),
    #     record.get("COLLECTED_AT"),
    # )

    return tuple(
        record[column] if column == "RAW_RECORD_ID"
        else record.get(column)
        for column in RAW_COLUMNS
    )

def build_source_expressions():
    """
    Build SQL expressions for the 13 RAW columns.

    Normal columns: %s
    COLLECTED_AT: TO_TIMESTAMP_NTZ(%s)
    """
    expressions = []

    for column in RAW_COLUMNS:

        # check if the column is COLLECTED_AT and use TO_TIMESTAMP_NTZ for that column
        if column == "COLLECTED_AT":
            expressions.append("TO_TIMESTAMP_NTZ(%s)")

        # handle the rest of columns
        else:
            expressions.append("%s")

    # Join expressions into one string separated by ", "
    return ", ".join(expressions)


def build_source_select():
    """
    Return the SELECT clause for the MERGE source.
    """

    expressions = build_source_expressions().split(", ")

    select_parts = []

    # Get SQL expressions from previous helper. Using zip to pair each expression with its corresponding column in RAW_COLUMNS
    for column, expression in zip(RAW_COLUMNS, expressions):

        # Combine expression with its column alias
        select_parts.append(f"{expression} AS {column}")
  
    # Join all SELECT parts with ", "
    return "SELECT " + ", ".join(select_parts)

def build_merge_sql():
    """
    Build the SQL statement for merging rental records into the RAW.RENTAL_LISTINGS table."""
    columns_sql = ", ".join(RAW_COLUMNS)

    source_select = build_source_select()

    values_sql = ", ".join(
        f"source.{column}"
        for column in RAW_COLUMNS
    )

    return f"""
    MERGE INTO STUDENT_RENTAL_DB.RAW.RENTAL_LISTINGS AS target

    USING (
        {source_select}
    ) AS source

    ON target.RAW_RECORD_ID = source.RAW_RECORD_ID

    WHEN NOT MATCHED THEN
        INSERT ({columns_sql})
        VALUES ({values_sql})
    """