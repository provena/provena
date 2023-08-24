from pydantic import BaseModel
import json
from typing import Dict, Any


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))
