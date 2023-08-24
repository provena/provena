from pydantic2ts import generate_typescript_defs
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum
import tempfile
import os
import shutil

SHARED_INTERFACES_LOCATION = "../../utilities/packages/python/shared-interfaces/SharedInterfaces"
UI_RELATIVE_BASE = "../.."
POSTFIX = "src/shared-interfaces"


class UI(str, Enum):
    LANDING_PORTAL = "LANDING_PORTAL"
    DATA_STORE = "DATA_STORE"
    REGISTRY = "REGISTRY"
    PROV_STORE = "PROV_STORE"
    REACT_LIBS = "REACT_LIBS"
    
class SOURCE(str, Enum):
    APIResponses = "APIResponses" 
    AuthAPI = "AuthAPI" 
    DataStoreAPI = "DataStoreAPI" 
    HandleAPI = "HandleAPI" 
    HandleModels = "HandleModels" 
    ProvenanceAPI = "ProvenanceAPI" 
    ProvenanceModels = "ProvenanceModels" 
    RegistryAPI = "RegistryAPI" 
    RegistryModels = "RegistryModels" 
    AsyncJobModels = "AsyncJobModels"
    AsyncJobAPI = "AsyncJobAPI"
    SearchAPI = "SearchAPI" 
    SharedTypes = "SharedTypes" 
    
UI_TO_PATH : Dict[UI, str] = {
    UI.LANDING_PORTAL : "landing-portal-ui",
    UI.DATA_STORE : "data-store-ui",
    UI.REGISTRY : "registry-ui",
    UI.PROV_STORE : "prov-ui",
    UI.REACT_LIBS : "utilities/packages/typescript/react-libs",
}

def source_to_exported_name(source :SOURCE) -> str:
    return source.value +".ts"

def source_to_python_source_name(source :SOURCE) -> str:
    return source.value +".py"

@dataclass
class ExportDefinition():
    python_module_location: str
    export_file_location: str

def construct_target_path(source: SOURCE, ui: UI) -> ExportDefinition:
    # where are we targeting?
    ui_target_path = UI_TO_PATH[ui]
    exported_name = source_to_exported_name(source)
    
    return ExportDefinition(
        python_module_location=os.path.join(SHARED_INTERFACES_LOCATION,source_to_python_source_name(source)),
        export_file_location=os.path.join(UI_RELATIVE_BASE, ui_target_path, POSTFIX, exported_name)
    )
    
def construct_copy_from_to_paths(source: SOURCE, ui: UI, tmpdirname: str) -> Tuple[str, str]:
    # where are we targeting?
    ui_target_path = UI_TO_PATH[ui]
    exported_name = source_to_exported_name(source)
    
    source_file = os.path.join(tmpdirname, exported_name)
    export_location = os.path.join(UI_RELATIVE_BASE, ui_target_path, POSTFIX, exported_name)
    
    return (source_file, export_location)

def perform_copy(from_path: str, to_path: str):
    print(f"Copying from {from_path} to {to_path}...")
    shutil.copyfile(src=from_path, dst=to_path)
    
def construct_target_path_fixed_output_dir(source: SOURCE, output_path: str) -> ExportDefinition:
    # where are we targeting?
    exported_name = source_to_exported_name(source)
    
    return ExportDefinition(
        python_module_location=os.path.join(SHARED_INTERFACES_LOCATION,source_to_python_source_name(source)),
        export_file_location=os.path.join(output_path, exported_name)
    )
    
ALL_SOURCES : List[SOURCE] = [
    SOURCE.APIResponses, 
    SOURCE.AuthAPI, 
    SOURCE.DataStoreAPI, 
    SOURCE.HandleAPI, 
    SOURCE.HandleModels, 
    SOURCE.ProvenanceAPI, 
    SOURCE.ProvenanceModels, 
    SOURCE.AsyncJobAPI, 
    SOURCE.AsyncJobModels, 
    SOURCE.RegistryAPI, 
    SOURCE.RegistryModels, 
    SOURCE.SearchAPI, 
    SOURCE.SharedTypes, 
]
    
TARGETS: Dict[UI, List[SOURCE]] = {
    UI.LANDING_PORTAL : [
            SOURCE.RegistryAPI,
            SOURCE.RegistryModels,
            SOURCE.SearchAPI,
            SOURCE.APIResponses,
            SOURCE.AuthAPI,
            SOURCE.DataStoreAPI
    ],
    UI.DATA_STORE : [
            SOURCE.RegistryAPI,
            SOURCE.SearchAPI,
            SOURCE.APIResponses,
            SOURCE.AuthAPI,
            SOURCE.DataStoreAPI
    ],
    UI.REGISTRY : [
            SOURCE.AuthAPI,
            SOURCE.SearchAPI,
            SOURCE.RegistryModels,
            SOURCE.RegistryAPI,
            SOURCE.APIResponses,
        ],
    UI.PROV_STORE : [
            SOURCE.RegistryAPI,
            SOURCE.RegistryModels,
            SOURCE.ProvenanceModels,
            SOURCE.ProvenanceAPI,
            SOURCE.SearchAPI,
            SOURCE.APIResponses,
            SOURCE.AuthAPI,
            SOURCE.DataStoreAPI
        ],
    UI.REACT_LIBS : ALL_SOURCES,
}

# export all sources to a temp directory 
with tempfile.TemporaryDirectory() as tmpdirname:
    # export all interfaces into a tmp dir once
    for source in ALL_SOURCES:
        export_def = construct_target_path_fixed_output_dir(
            source = source,
            output_path = tmpdirname
        ) 
        
        # Do this once
        print(f"Exporting from {export_def.python_module_location} ---> {export_def.export_file_location}...")
        generate_typescript_defs(
           module=export_def.python_module_location,
           output=export_def.export_file_location  
        )


    copy_list : List[Tuple[str,str]] = []
    for ui, source_list in TARGETS.items():
        for source in source_list:
            copy_list.append(
                construct_copy_from_to_paths(source=source, ui=ui, tmpdirname=tmpdirname) 
            )

    for from_path, to_path in copy_list:
        perform_copy(from_path, to_path)
