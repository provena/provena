from pydantic import BaseModel
from typing import Dict, Any
import json
from datetime import datetime


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))


def timestamp() -> int:
    return int(datetime.now().timestamp())
