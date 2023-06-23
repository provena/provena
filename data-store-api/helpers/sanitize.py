def sanitize_name(input_name: str) -> str:
    """
    Function Description
    --------------------

    Given a raw name will sanitize for use as a URI


    Arguments
    ----------
    input_name : str
        The input name

    Returns
    -------
    str
        The output sanitized name



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return input_name.strip().replace(" ", "_").upper()


def sanitize_handle(input_handle: str) -> str:
    """
    Function Description
    --------------------

    Given a raw handle name will sanitize for use as a URI


    Arguments
    ----------
    input_handle : str
        The input handle

    Returns
    -------
    str
        The output sanitized handle for file names

    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Replaces full stops and slashes with dashes
    # strips white space
    return input_handle.replace('.', '-').replace('/', '-').strip()