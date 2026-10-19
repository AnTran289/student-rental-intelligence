def validate_schema(actual_columns, required_columns):
    # turn collections into sets
    required_set = set(required_columns)
    actual_set = set(actual_columns)

    # get the elements appears in required_set that do NOT appear in actual_set
    missing_columns = required_set.difference(actual_set)

    # Use len() to check missing columns. If length > 0 means is_valid will be False
    is_valid = len(missing_columns) == 0

    # Return results respecting required contract
    return {
        "is_valid": is_valid,
        "missing_columns": sorted(missing_columns)
    }