from pydantic import BaseSettings
from enum import Enum

class SearchableObject(str, Enum):
    DATA_STORE_ITEM = "DATA_STORE_ITEM"
    REGISTRY_ITEM = "REGISTRY_ITEM"

class Config(BaseSettings):
    # required env variables
    
    # the full name of the search domain 
    search_domain_name: str
    
    # the index name
    search_index: str

    # needs to the string record ID
    record_id_field: str

    # the type of record this streamer is processing - used to help derive
    # searchable record versions with predictable structure 
    item_type : SearchableObject
    
    # the name of the field to output to when linearised
    linearised_field: str
   
    # default config 
    # the AWS region 
    aws_region: str = "ap-southeast-2"


config = Config()
