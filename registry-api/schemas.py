from SharedInterfaces.RegistryModels import *
from route_models import ItemModelTypeVar

DISPLAY_NAME_LABEL = "Enter a brief name, label or title for this resource."


# Can adjust mapping from model -> schema overrides here
UI_SCHEMA_OVERRIDES: Dict[ItemModelTypeVar, Dict[str, Any]] = {  # type: ignore
    ItemModelRun: {
        # This should not be registered through UI
    },
    ItemStudy: {
        "ui:title": "Study",
        "display_name": {
            "ui:description": DISPLAY_NAME_LABEL,
        },
        'title': {
            'ui:description': "Please provide a complete title which identifies this Study.",
        },
        'description': {
            'ui:description': "Please provide any additional relevant description about this Study activity."
        },
    },
    ItemOrganisation: {
        "ui:title": "Organisation",
        "display_name": {
            "ui:description": DISPLAY_NAME_LABEL,
        },
        # Should we use ROR selector? This isn't implement in front end reg yet
        'ror': {
            'ui:description': "If the organisation has a ROR, provide the full URL here.",
        },
        'name': {
            'ui:description': "Enter the name of the organisation."
        },
        'ror': {
            'ui:title': "Organisation ROR",
            'ui:description': "Optionally specify the organisation's ROR.",
            'ui:field': "autoCompleteRORLookup"
        }
    },
    ItemPerson: {
        "ui:title": "Person",
        "display_name": {
            "ui:description": "Enter a display name for this person."
        },
        'first_name': {
            'ui:description': "What is this person's first name?"
        },
        'last_name': {
            'ui:description': "What is this person's last name?"
        },
        'email': {
            'ui:description': "What is this person's email address?"
        },
        'orcid': {
            'ui:description': 'Optionally provide an ORCID using the search tool below.',
            'ui:field': "autoCompleteOrcid"
        },
        'ethics_approved': {
            'ui:field': "personEthicsTickBox",
            'ui:description': "Have you received consent and been granted permission from the person to be registered in the registry?"
        }
    },
    ItemModel: {
        "ui:title": "Model",
        "display_name": {
            "ui:description": DISPLAY_NAME_LABEL,
        },
        "name": {
            "ui:description": "Enter a name for the software model."
        },
        "description": {
            "ui:description": "Provide a description of the model. You can include as much detail as required.",
            "ui:widget": "TextareaWidget"
        },
        "documentation_url": {
            "ui:description": "Provide a fully qualified URL (e.g. include https) to the site which hosts documentation about the model."
        },
        "source_url": {
            "ui:description": "Provide a fully qualified URL (e.g. include https) to the site which hosts the source code for this model."
        }
    },
    ItemModelRunWorkflowTemplate: {
        "ui:title": "Model Run Workflow Template",
        "display_name": {
            "ui:description": DISPLAY_NAME_LABEL,
        },
        "software_id": {
            "ui:description": "Select a registered model from the search tool below.",
            "ui:field": "autoCompleteModelLookup"
        },
        "software_version": {
            "ui:description": "What version of the software does this workflow template refer to? e.g. '1.0.3'",
        },
        "input_templates": {
            "ui:title": "Input Dataset Templates",
            "ui:description": "Provide a list of the model's expected inputs.",
            "items": {
                "ui:title": "Input Template",
                "template_id": {
                    "ui:description": "Use the search tool below to select a registered dataset template.",
                    "ui:field": "autoCompleteDatasetTemplateLookup"
                },
                "optional": {
                    "ui:description": "Tick this box if the dataset template is optional."
                }
            }
        },
        "output_templates": {
            "ui:title": "Output Dataset Templates",
            "ui:description": "Provide a list of the model's expected outputs.",
            "items": {
                "ui:title": "Output Template",
                "template_id": {
                    "ui:description": "Use the search tool below to select a registered dataset template.",
                    "ui:field": "autoCompleteDatasetTemplateLookup"
                },
                "optional": {
                    "ui:description": "Tick this box if the dataset template is optional."
                }
            }
        },
        "annotations": {
            "ui:widget": "annotationsOverride",
            "ui:title": "Model Run Annotations",
            "disableOptional" : True,
            "ui:description": "If you would like model runs to require or optionally provide additional user defined annotations, you can include them here. These annotations will be searchable.",
            "items": {
                "required": {
                    "ui:title": "Required annotations",
                    "ui:description": "These annotations must have a value for every model run."
                },
                "optional": {
                    "ui:title": "Optional annotations",
                    "ui:description": "These annotations are optional - they can be provided but are not required for every model run."
                },
            }
        }
    },
    ItemDatasetTemplate: {
        "ui:title": "Dataset Template",
        "display_name": {
            "ui:description": DISPLAY_NAME_LABEL,
        },
        "description": {
            "ui:description": "Enter a description about the dataset template. Please include any contextual information about the expected contents of conforming datasets.",
            "ui:widget": "TextareaWidget"
        },
        "defined_resources": {
            "ui:description": "Defined resources have a known and consistent file path. E.g. dataset A should contain 'parameters.csv' at path 'inputs/parameters.csv'.",
            "items": {
                "path": {
                    "ui:description": "Provide the relative file path to the resource. E.g. 'inputs/parameters.csv'.",
                },
                "description": {
                    "ui:description": "Provide a description of the defined resource.",
                    "ui:widget": "TextareaWidget"
                },
                "optional": {
                    "ui:description": "Is this resource optional? By default, it is required."
                },
                "usage_type": {
                    "ui:description": "What kind of resource is this? How is it being used? Select from the options."
                },
                "is_folder": {
                    "ui:title": "Folder or file?",
                    "ui:description": "By default, resources are files. If you would like to specify a folder instead, use this option."
                },
                "additional_metadata": {
                    "ui:description": "You can optionally provide additional annotations to this record.",
                    "ui:field": "datasetTemplateMetadataOverride",
                }
            }
        },
        "deferred_resources": {
            "ui:description": "Deferred resources have a file path which is unknown until model run time, or is variable between model runs. Deferred resources are uniquely identified by a key. E.g. dataset A should contain a parameter file with a name determined at model run time e.g. resource with key 'parameters' at path 'inputs/parameter_file378.txt'.",
            "items": {
                "key": {
                    "ui:description": "Provide a unique (within this record) key for this resource."
                },
                "description": {
                    "ui:description": "Provide a description of the deferred resource.",
                },
                "optional": {
                    "ui:description": "Is this resource optional? By default, it is required."
                },
                "usage_type": {
                    "ui:description": "What kind of resource is this? How is it being used? Select from the options."
                },
                "is_folder": {
                    "ui:title": "Folder or file?",
                    "ui:description": "By default, resources are files. If you would like to specify a folder instead, use this option."
                },
                "additional_metadata": {
                    "ui:field": "datasetTemplateMetadataOverride",
                    "ui:description": "You can optionally provide additional annotations to this record."
                }
            }
        }
    },
    ItemDataset: {
    }
}

# Can adjust mapping from model -> schema overrides here
JSON_SCHEMA_OVERRIDES: Dict[ItemModelTypeVar, Dict[str, Any]] = {  # type: ignore
}
