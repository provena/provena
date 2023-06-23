from pydantic import BaseModel
from typing import Optional
try:
    from SharedInterfaces.SharedTypes import StatusResponse
    from SharedInterfaces.HandleModels import *
except:
    from .SharedTypes import StatusResponse
    from .HandleModels import *


class ValueRequestBase(BaseModel):
    value_type: ValueType
    value: str


class AddValueRequest(ValueRequestBase):
    id: str


class AddValueIndexRequest(ValueRequestBase):
    id: str
    index: int


class MintRequest(ValueRequestBase):
    pass


class ModifyRequest(BaseModel):
    id: str
    index: int
    value: str


class RemoveRequest(BaseModel):
    id: str
    index: int


class ListResponse(BaseModel):
    ids: List[str]


MintResponse = Handle
AddValueResponse = Handle
AddValueIndexResponse = Handle
GetResponse = Handle
ModifyResponse = Handle
RemoveResponse = Handle
