def prepare_records(records):
    """
    Transform CSV dictionaries into records that
    are ready to be mapped into Snowflake raw table. 
    """

    # new_records = []
    # for record in records:
    #     new_record = {
    #         key.upper(): value
    #         for key, value in record.items()
    #     }
    #     new_records.append(new_record)
    # return new_records
    

    # List comprehension version of the above for loop
    return [
        {key.upper(): value for key, value in record.items()} for record in records
    ]