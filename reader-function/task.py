from google.cloud import datastore


def datastoreTypeCast(value, valueType):
    """
    Perform type casting on a value based on the specified valueType.

    This function takes a value and a valueType as parameters and returns the
    value casted to the specified type. The function supports casting to common
    data types like string, integer, double, boolean, key, and null.

    Args:
        value: The value to be casted.
        valueType (str): The target type to which the value should be casted.
            Possible values are: "string", "integer", "double", "boolean", "key",
            and "null".

    Returns:
        The input value casted to the specified type.

    Raises:
        ValueError: If the provided valueType is not one of the supported types.

    Example:
        value = "42"
        valueType = "integer"
        casted_value = datastoreTypeCast(value, valueType)
        # Result: 42 (as an integer)
    """
    if valueType == "string":
        return str(value)
    elif valueType == "integer":
        return int(value)
    elif valueType == "double":
        return float(value)
    elif valueType == "boolean":
        return bool(value)
    elif valueType == "key":
        return value  # Assuming key is a valid type
    elif valueType == "null":
        return None
    else:
        raise ValueError("Invalid valueType")


def run(event):
    query_kind = event.get('query_kind')

    if query_kind == None:
        raise "query_kind is required"

    result_key = event.get('result_key')

    if result_key == None:
        raise "result_key is required"

    query_filter = event.get('query_filter')
    query_limit = int(event.get('query_limit'))

    client = datastore.Client()
    query = client.query(kind=query_kind)

    if query_filter != None:
        filters = query_filter.split(";")
        for f in filters:
            [field, operator, value, valueType] = f.split(",")
            query.add_filter(
                field, operator, datastoreTypeCast(value, valueType))

    results = list(query.fetch(limit=query_limit))

    injectResults = []

    for entity in results:
        entity_properties = entity.items()
        injectResults.append(dict(entity_properties))

    event.set(result_key, injectResults)

    return
