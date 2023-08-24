from pydantic import BaseModel
from typing import Dict, Any
import json

def py_to_dict(item: BaseModel) -> Dict[str, Any]:
    return json.loads(item.json(exclude_none=True))