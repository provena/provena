from pydantic import BaseModel
from typing import Dict, Any
import json


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))
