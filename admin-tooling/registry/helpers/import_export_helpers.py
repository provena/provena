from typing import Optional
from typing import Dict


def yes_or_no(query: str) -> bool:
    """yes_or_no
    helper function to display y/n confirmation.

    Arguments
    ----------
    query : str
        The question to pose

    Returns
    -------
     : bool
    Returns true iff valid input of y/yes.
    Returns false iff valid input of n/no.


    See Also (optional)
    --------

    Examples (optional)
    --------
    """
    valid_response = False
    response: Optional[bool] = None
    valid_responses = ["N", "Y", "YES", "NO"]

    while not valid_response:
        possible_response = input(query + " [Y/N]\n")
        filtered_response = possible_response.upper().strip()
        if filtered_response in valid_responses:
            valid_response = True
            if filtered_response in ["YES", "Y"]:
                response = True
            else:
                response = False
        else:
            print(f"Invalid response. Please enter one of {valid_responses}")
    assert response is not None
    return response