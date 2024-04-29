from pydantic import BaseModel
from typing import Dict, Any
import json
from httpx._models import Response
from ProvenaInterfaces.HandleModels import *


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))


def get_property_by_index(handle: Handle, index: int) -> HandleProperty:
    for prop in handle.properties:
        if prop.index == index:
            return prop

    raise Exception(f"Couldn't find property with index {index}.")


def check_no_property_by_index(handle: Handle, index: int) -> None:
    for prop in handle.properties:
        if prop.index == index:
            raise Exception(f"Found property with index {index}.")


def parse_handle_object_successfully(response: Response) -> Handle:
    # check status code
    status_code = response.status_code
    if status_code != 200:
        error_message = "Unknown"
        try:
            error_message = response.json()['detail']
        except:
            pass
        raise Exception(f"Expected 200 code, got {status_code}. Details: {error_message}.")

    # return handle object
    return Handle.parse_obj(response.json())


def parse_handle_unsuccessfully(response: Response) -> None:
    # check status code
    status_code = response.status_code
    if status_code != 500:
        raise Exception(f"Expected 500 code, got {status_code}")
