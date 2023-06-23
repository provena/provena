import typer
import json
from config import *
from typing import List, Any, Dict
from helpers.indexing import modified_handler
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from helpers.get_aws_auth import get_auth
import logging

logging.basicConfig(level=logging.INFO)

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer()


@app.command()
def reindex_registry(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    input: typer.FileText = typer.Argument(
        ...,
        help=f"The input JSON file which was dumped from the registry using the import export tools."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # this sets up the signed AWS auth
    auth = get_auth(region=env.aws_region)

    # load the json items
    items: List[Dict[str, Any]] = json.loads(input.read())

    # pull out the item payload
    payloads = list(map(lambda item: item['item_payload'], items))

    # iterate through the items and run the index operation
    modified_handler(
        awsauth=auth,
        records=payloads,
        record_id_field="id",
        index_name=INDEX_MAP[Indexes.REGISTRY],
        search_service_endpoint=env.search_service_endpoint,
        item_type=SearchableObject.REGISTRY_ITEM
    )


if __name__ == "__main__":
    app()
