def get_dict_nested_value(x, *keys):
    """
    Get a value nested inside a dict
    :param x: The dict to extract the value from
    :param keys: Any number of string arguments representing the nested keys to search through
    :return: The value at the nested location or None if not found
    """
    if not x:
        return None

    for k in keys:
        x = x.get(k)
        if not x:
            return {}
    return x
