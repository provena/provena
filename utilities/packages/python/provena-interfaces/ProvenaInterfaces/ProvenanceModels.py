from pydantic import BaseModel, root_validator, validator
from typing import List, Optional, Dict, Any
from enum import Enum

# Base type alias for identified resources
IdentifiedResource = str

# Each of the various resource types which are associated with an ID
ModellerResource = IdentifiedResource
OrganisationResource = IdentifiedResource
ModelResource = IdentifiedResource
ModelRunWorkflowTemplateResource = IdentifiedResource
DatasetTemplateResource = IdentifiedResource
DataStoreDatasetResource = IdentifiedResource


class DatasetType(str, Enum):
    DATA_STORE = "DATA_STORE"


# Type alias placeholders for more complex structure if required later
ResourcePath = str
ResourceSpecification = ResourcePath


class TemplatedDataset(BaseModel):
    # What template does this dataset adhere to?
    dataset_template_id: DatasetTemplateResource

    # The actual dataset which must have type
    # matching the above
    dataset_id: DataStoreDatasetResource

    # Reference to which kind of type - currently hard coded as data store
    dataset_type: DatasetType

    # If the template specifies deferred resources, then they should be
    # specified here - the keys of this dictionary are the specified keys in the
    # deferred resource definition within the workflow template
    resources: Optional[Dict[str, ResourceSpecification]] = None

    def make_searchable(self) -> str:
        resource_items = []
        if self.resources:
            for k, v in self.resources.items():
                resource_items.append(k)
                resource_items.append(v)

        return " ".join(
            [
                self.dataset_template_id,
                self.dataset_id,
                " ".join(resource_items)
            ]
        )


class AssociationInfo(BaseModel):
    # What modeller produced this record - agent handle ID
    modeller_id: ModellerResource
    # Optionally, can specify an organisation that this model
    # run was requested by - agent ID in registry
    requesting_organisation_id: Optional[OrganisationResource]
    # TODO add non registrant attributions i.e. collaborators

    def make_searchable(self) -> str:
        elems = [self.modeller_id]
        if self.requesting_organisation_id:
            elems.append(self.requesting_organisation_id)
        return " ".join(elems)


class ModelRunRecord(BaseModel):
    # What workflow template does this model run fulfil?
    workflow_template_id: ModelRunWorkflowTemplateResource
    
    # RRAPIS-1580 - move this to the run itself to avoid weird churn on template
    # Optional to specify but first class - allows for whatever scheme makes
    # sense for user e.g. git hash
    model_version: Optional[str] = None

    # inputs (datasets, config, param files) - must fulfil template
    inputs: List[TemplatedDataset]
    outputs: List[TemplatedDataset]

    # custom user annotations - these are configured in the workflow template
    # and resolved here - can contain additional annotations, optional
    # annotations, but must have all required annotations
    annotations: Optional[Dict[str, str]] = None

    # pre canned annotations

    # model run display name
    display_name: str

    # provide a description of this run
    description: str

    # is this model run part of a study?
    study_id: Optional[str] = None

    # Associations of the record
    associations: AssociationInfo

    # Activity time metadata
    # unix timestamp (epoch)
    start_time: int
    # unix timestamp (epoch)
    end_time: int

    # validate start time is before end time using root validator
    @root_validator(pre=False)
    def validate_start_and_end(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start_time = values.get('start_time')
        end_time = values.get('end_time')

        if start_time is not None and end_time is not None:
            if start_time > end_time:
                raise ValueError(
                    f"The 'start_time' value ({start_time}) must be smaller than or equal to the 'end_time' value ({end_time}).")
        return values

    # validate display name and description are not empty strings using the same validator
    @validator("display_name", "description")
    def string_must_not_be_empty(cls: Any, v: str) -> str:
        if v == "":
            raise ValueError("string must not be empty")
        return v

    def make_annotations_searchable(self) -> str:
        annotation_strings = []
        if self.annotations:
            for k, v in self.annotations.items():
                annotation_strings.append(k + " " + v)
        return " ".join(annotation_strings)

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return [
            "workflow_template_id",
            "model_version",
            "display_name",
            "description",
            "inputs",
            "outputs",
            "annotations",
            "associations",
            "start_time",
            "end_time",
        ]

    def get_search_ready_object(self) -> Dict[str, str]:
        # helper function for search utilities
        fields: Dict[str, str] = {
            "workflow_template_id": self.workflow_template_id,
            "display_name": self.display_name,
            "model_version": self.model_version or "",
            "description": self.description or "",
            "inputs": " ".join([i.make_searchable() for i in self.inputs]),
            "outputs": " ".join([o.make_searchable() for o in self.outputs]),
            "annotations": self.make_annotations_searchable(),
            "associations": self.associations.make_searchable(),
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
        }
        return fields


# Deprecated alternatives to data store type (for now)
"""
class URLDatasetCredentials(BaseModel):
    # TODO what do we do with creds?
    None


class URLDatasetResource(BaseModel):
    # TODO how do we define a URL dataset?
    url: AnyHttpUrl
    credentials: Optional[URLDatasetCredentials]


class FileSystemResource(BaseModel):
    # TODO where does this context come from
    # not really supported now
    file_system_location: str
    filename_regex: Optional[str] = None
    
    
class DatasetType(str, Enum):
    DATA_STORE = "DATA_STORE"
    URL = "URL"
    # TODO this isn't really supported yet
    # but could be a placeholder for automated contexts
    FILE_SYSTEM = "FILE_SYSTEM"


# Collect all possible dataset types into union type
dataset_types = Union[DataStoreDatasetResource,
                      URLDatasetResource, FileSystemResource]

# Map between dataset type enum and their class
dataset_type_class_map: Dict[DatasetType, Type[dataset_types]] = {
    DatasetType.DATA_STORE: DataStoreDatasetResource,
    DatasetType.URL: URLDatasetResource,
    DatasetType.FILE_SYSTEM: FileSystemResource
}

# Collect all possible dataset types into union type
dataset_types = Union[DataStoreDatasetResource]

# Map between dataset type enum and their class
dataset_type_class_map: Dict[DatasetType, Type[dataset_types]] = {
    DatasetType.DATA_STORE: DataStoreDatasetResource,
}


@root_validator(skip_on_failure=True)
def check_dataset_type_matches(cls, values: Dict[str, Any]) -> Dict[str, Any]:
    # Checks that the dataset has type specified by looking up
    # the dataset type in the provided dataset_type_class_map defined
    # above
    if not values.get('dataset_type'):
        raise ValueError("Did not provide a dataset_type.")
    if not values.get('dataset'):
        raise ValueError("Did not provide a dataset value.")

    # get relevant fields
    dataset_type: DatasetType = values['dataset_type']
    dataset: dataset_types = values['dataset']

    # get the proper type
    proper_class = dataset_type_class_map[dataset_type]

    # check the dataset is an instance of this type
    if not (isinstance(dataset, proper_class)):
        raise ValueError(
            "The provided dataset does not have class which matches the dataset_type provided.")

    # return the values, all appears well
    return values
"""
