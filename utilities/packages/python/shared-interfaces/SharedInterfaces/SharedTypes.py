from pydantic import BaseModel 
from enum import Enum
from typing import Optional

class Status(BaseModel):
    success : bool 
    details : str

class StatusResponse(BaseModel):
    status: Status
    
    
class ImportMode(str, Enum):
    # Will never change existing entries Can only add new entries
    ADD_ONLY = "ADD_ONLY"

    # Will add new entries, or overwrite existing if they match
    ADD_OR_OVERWRITE = "ADD_OR_OVERWRITE"

    # Only allows updating of existing entries
    OVERWRITE_ONLY = "OVERWRITE_ONLY"

    # Will add new entries, overwrite existing and enforce there being no
    # unmatched entries
    SYNC_ADD_OR_OVERWRITE = "SYNC_ADD_OR_OVERWRITE"

    # Will perform a full sync meaning new additions added, existing overwritten
    # and left over unmatched entries deleted
    SYNC_DELETION_ALLOWED = "SYNC_DELETION_ALLOWED"


class VersionDetails(BaseModel):
    commit_id: Optional[str]
    commit_url: Optional[str]
    tag_name: Optional[str]
    release_title: Optional[str]
    release_url: Optional[str]