from dataclasses import dataclass
from ProvenaInterfaces.AsyncJobModels import JobSnsPayload, JobStatus
from typing import Callable, Optional, Dict, Any
from EcsSqsPythonTools.Settings import JobBaseSettings


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
CallbackFunc = Callable[[JobSnsPayload, JobBaseSettings], CallbackResponse]
