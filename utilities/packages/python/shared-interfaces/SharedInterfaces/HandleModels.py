from pydantic import BaseModel
from enum import Enum
from typing import List


class ValueType(str, Enum):
    DESC = "DESC"
    URL = "URL"


class HandleProperty(BaseModel):
    type: ValueType
    value: str
    index: int


class Handle(BaseModel):
    id: str
    properties: List[HandleProperty]
