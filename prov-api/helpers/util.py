from pydantic import BaseModel
import json
from typing import Dict, Any, List

from ProvenaInterfaces.RegistryAPI import ItemBase, ItemSubType

def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json(exclude_none=True))



# Wrapper around the validate_by method for study and model runs 
