from typing import List, Callable, Dict
from ProvenaInterfaces.RegistryModels import ItemModelRun
from dataclasses import dataclass
from helpers.type_aliases import GetAuthFunction


@dataclass
class EndpointContext:
    endpoint: str
    auth: GetAuthFunction


ModelRunsType = List[ItemModelRun]
CSVRow = Dict[str, str]
CSVType = List[CSVRow]
Timezone = str
ReportGenerator = Callable[[ModelRunsType, EndpointContext, Timezone], CSVType]
