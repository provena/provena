from datetime import datetime

def get_timestamp() -> int:
    """    get_timestamp
        Gets the current timestamp as an integer
        for use in dynamoDB timestamps

        Returns
        -------
         : int
            The current unix time timestamp in seconds

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return int(datetime.now().timestamp())


def iso_to_epoch(val: str) -> int:
    """Convert iso formatted datetime string (optionally formatted with '/' into
    epoch timestamp integer

    Parameters
    ----------
    val : str
        The iso formatted time. <YYYY-MM-DD HH:MM:SS+HH:MM>. e.g. "2011-12-03
        10:15:30+11:00". Optionally use '/' instead of '-' in the date.

    Returns
    -------
    int
        corresponding EPOCH timestamp.
    """
    try: 
        return int(datetime.fromisoformat(val.replace('/','-')).timestamp())
    except Exception:
        raise Exception("Validation error when parsing provided time, expected format: YYYY-MM-DD HH:MM:SS+HH:MM.")


def epoch_to_iso(time: int) -> str:
    """Receives an EPOCH time stamp and returns the associated ISO formatted time in UTC.

    Parameters
    ----------
    time : int
        The EPOCH time stamp to convert into ISO format in UTC.

    Returns
    -------
    str
        The corresponding ISO formatted string in UTC
    """

    # return datetime.fromtimestamp(time).isoformat(sep=" ", ))
    return str(datetime.fromtimestamp(time).astimezone())
