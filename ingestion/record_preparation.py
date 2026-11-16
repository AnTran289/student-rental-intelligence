# def prepare_records(records):
#     """
#     Transform CSV dictionaries into records that
#     are ready to be mapped into Snowflake raw table.
#     """

    # new_records = []
    # for record in records:
    #     new_record = {
    #         key.upper(): value
    #         for key, value in record.items()
    #     }
    #     new_records.append(new_record)
    # return new_records


    # List comprehension version of the above for loop
    # return [
    #     {key.upper(): value for key, value in record.items()} for record in records
    # ]

# Postgres
def prepare_records(records):
    """
    Normalize CSV record keys for PostgreSQL loading.
    """
    return [
        {key.lower(): value for key, value in record.items()}
        for record in records
    ]

# records = [
#     {"RAW_RECORD_ID": "L001", "WEEKLY_RENT": "$290"},
#     {"RAW_RECORD_ID": "L002", "WEEKLY_RENT": "$250"}
# ]

# # result = prepare_records(records)

# # print(result)
# # print("Input count:", len(records))
# # print("Output count:", len(result))
