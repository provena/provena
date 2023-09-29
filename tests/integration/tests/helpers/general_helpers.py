from typing import Any, Dict, Union, List
from copy import deepcopy
import json
from pydantic import BaseModel
from datetime import datetime
from requests import Response

def assert_x_ok(res: Response, desired_status_code: int = 200) -> None:
    status_code = res.status_code
    text = res.text
    if status_code != desired_status_code:
        raise Exception(
            f"Failed request, expected {desired_status_code}, got {status_code}. Text: {text}")


def assert_200_ok(res: Response) -> None:
    assert_x_ok(res=res, desired_status_code=200)


def display_failed_cleanups(failed_cleanups: Any) -> None:
    print("--- FAILED CLEANUPS ---")
    for x in failed_cleanups:
        print(x)


def py_to_dict(item: BaseModel) -> Dict[str, Any]:
    return json.loads(item.json(exclude_none=True))


def filtered_none_deep_copy(input: Any) -> Union[Dict[Any, Any], List[Any], Any]:
    """
    Helper function to make a deepcopy of a dictionary recursively - not
    including any None objects. This is because dictionary comparisons are
    sensitive to None/null values in the pydantic model/json object. We aren't
    concerned about Nones vs not including for the purposes of these test.

    Parameters
    ----------
    input : Any
        Either a dictionary or an object which will be returned (think leaf
        node)

    Returns
    -------
    Union[Dict[Any, Any], Any]
        Either a dictionary (i.e. recursively) or a leaf node 
    """
    # if dictionary - copy recursively
    if isinstance(input, dict):
        # produce a new dictionary
        new_dict: Dict[Any, Any] = {}
        # iterate through key values
        for k, v in input.items():
            # if none - don't include
            if v is None or v == "null":
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_dict[k] = filtered_none_deep_copy(v)
        return new_dict

    # if list - iterate through and filter none
    # returning recursively for elements
    if isinstance(input, list):
        new_list = []
        for v in input:
            # if none - don't include
            if v is None:
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_list.append(filtered_none_deep_copy(v))
        return new_list
    else:
        # Return a native copy of the leaf node
        return deepcopy(input)


def check_equal_models(m1: BaseModel, m2: BaseModel) -> None:
    """

    Checks that the two pydantic models are equal by converting to dictionary,
    dropping None values and deep comparing

    Parameters
    ----------
    m1 : BaseModel
        Model 1
    m2 : BaseModel
        Model 2
    """
    assert filtered_none_deep_copy(py_to_dict(
        m1)) == filtered_none_deep_copy(py_to_dict(m2))
    
def get_timestamp() -> int:
    """

    Gets current unix timestamp

    Returns
    -------
    int
        Timestamp
    """
    return int(datetime.now().timestamp())


def check_current_with_buffer(ts: int, buffer: int = 5) -> None:
    """

    Checks that the desired timestamp is within buffer  +/- of current timestamp

    Parameters
    ----------
    ts : int
        The target timestamp
    buffer : int, optional
        The seconds buffer, by default 5
    """
    current = get_timestamp()
    assert ts > current - buffer and ts < current + buffer
