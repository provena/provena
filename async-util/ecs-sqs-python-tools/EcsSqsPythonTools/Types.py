from dataclasses import dataclass
from ProvenaInterfaces.AsyncJobModels import JobSnsPayload, JobStatus
from typing import Callable, Protocol, Optional, Dict, Any
from EcsSqsPythonTools.Settings import JobBaseSettings
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask


class CallbackBase(Protocol):
    status: JobStatus
    info: Optional[str]


@dataclass
class CallbackResponse():
    # The status of the response
    status: JobStatus
    # Any info if error
    info: Optional[str] = None
    # The result payload - must adhere to typed interface in shared interfaces
    result: Optional[Dict[str, Any]] = None
    

# A callback function takes a payload and settings, and returns the callback
# response
CallbackFunc = Callable[[JobSnsPayload, JobBaseSettings], CallbackBase]
