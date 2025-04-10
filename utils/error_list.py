def add_error_to_list(error_list, field, message):
    """ "
    "Add an error message to the error list."
    """
    error_list.append({
        "field": field,
        "message": message
    })