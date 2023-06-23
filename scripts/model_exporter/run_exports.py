from typing import List
from pydantic import BaseModel
from dataclasses import dataclass
import json


@dataclass
class ExportDefinition():
    model: BaseModel
    locations: List[str]


# Add items to this list if you want to export
# more models - the models must be 'instances'
# of the Model not definitions of a model. Definitions
# of a model are exported through the TypeScript
# interfaces.
exports: List[ExportDefinition] = [
    #ExportDefinition(
    #    model=RoleStructure.AUTHORISATION_MODEL,
    #    locations=[
    #        "../../landing-portal/src/model-exports/authorisation_model.json",
    #        "../../data-store-ui/src/model-exports/authorisation_model.json"
    #    ]
    #)
]


def write_model(model: BaseModel, location: str) -> None:
    """    write_model
        Given a pydantic model instance and a location, 
        will use the BaseModel json serialisation to dump
        the instance to that location. 

        Arguments
        ----------
        model : BaseModel
            The pydantic model
        location : str
            The file location relative to the working 
            directory of this script (cannot be run 
            from top level of project)

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Print out nice preview for logs
    model_string: str = str(model)
    printout: str = model_string
    preview_length: int = 50
    max_length: int = 120

    # Contract if necessary
    if len(model_string) > max_length:
        start = model_string[:preview_length]
        end = model_string[-preview_length:]
        printout = f"{start}...{end}"

    print(f"Exporting model:\n{printout}\nto {location}.\n")
    # Write model to given location
    with open(location, 'w') as f:
        f.write(
            json.dumps(
                json.loads(model.json()),
                indent=2
            )
        )


def write_model_to_locations(model: BaseModel, locations: List[str]) -> None:
    """    write_model_to_locations
        Given the model will distribute the write model
        function to the lists.

        Arguments
        ----------
        model : BaseModel
            The model to write
        locations : List[str]
            The list of locations to write it to

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # For each model, write location
    for loc in locations:
        write_model(model, loc)


def export_models() -> None:
    """    export_models
        The main script runner for this export. The purpose
        of this export is to complement the interface export
        process by adding the ability to export instances of a 
        pydantic model. The model will be in json which typescript
        can then import and parse as the exported interface. 
        This keeps the process safe and it is easy to update within
        a typed model specification.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    print("Starting model export.")
    # Export each of the export definitions
    for export in exports:
        write_model_to_locations(
            model=export.model,
            locations=export.locations
        )


if __name__ == "__main__":
    export_models()
