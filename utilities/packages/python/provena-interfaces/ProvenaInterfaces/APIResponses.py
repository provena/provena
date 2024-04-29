from pydantic import BaseModel
from typing import List, Union

class Detail(BaseModel): 
        loc : List[Union[int, str]]
        msg : str 
        type : str
        
class HTTPValidationError(BaseModel):
        detail : List[Detail]