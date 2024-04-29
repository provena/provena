import typer
import json
import requests
from config import *
from typing import List, Any, Optional, Dict
from helpers.get_aws_auth import get_auth
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from enum import Enum
from rich import print

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer()

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string


class HTTPMethods(str, Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


@app.command()
def manual_command(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    method: HTTPMethods = typer.Argument(
        ...,
        help=f"The HTTP method to run at the endpoint"
    ),
    endpoint: str = typer.Argument(
        ...,
        help=f"The full URL/endpoint to run method at."
    ),
    payload_file: Optional[typer.FileText] = typer.Option(
        None,
        help=f"The JSON payload to send with that method to the endpoint. Specify file path."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    auth = get_auth(region=env.aws_region)

    payload: Optional[Dict[str, Any]] = None

    if payload_file is not None:
        payload = json.loads(payload_file.read())

    if payload_file is not None:
        response = requests.request(
            method=method.value,
            url=endpoint,
            json=payload,
            auth=auth
        )
    else:
        response = requests.request(
            method=method.value,
            url=endpoint,
            auth=auth
        )
    try:
        response.raise_for_status()
        try:
            print(response.json())
        except:
            try:
                print(response.text)
            except:
                print(response)
    except requests.exceptions.HTTPError as he:
        print(f"Error occurred: {he}.")


@app.command()
def stage_index_command(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    method: HTTPMethods = typer.Argument(
        ...,
        help=f"The HTTP method to run at the endpoint"
    ),
    index: Indexes = typer.Argument(
        ...,
        help=f"Index to run command on"
    ),
    action: str = typer.Argument(
        ...,
        help=f"Postfix on <stage search endpoint>/index_name. Include / in the postfix."
    ),
    payload_file: Optional[typer.FileText] = typer.Option(
        None,
        help=f"The JSON payload to send with that method to the endpoint. Specify file path."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    auth = get_auth(region=env.aws_region)

    payload: Optional[Dict[str, Any]] = None

    if payload_file is not None:
        payload = json.loads(payload_file.read())

    index = INDEX_MAP[index]
    endpoint = f"{env.search_service_endpoint}/{index}{action}"

    if payload_file is not None:
        response = requests.request(
            method=method.value,
            url=endpoint,
            json=payload,
            auth=auth
        )
    else:
        response = requests.request(
            method=method.value,
            url=endpoint,
            auth=auth
        )
    try:
        response.raise_for_status()
        try:
            print(response.json())
        except:
            print(response)
    except requests.exceptions.HTTPError as he:
        print(f"Error occurred: {he}.")


@app.command()
def create_global_alias_index(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Creates a global alias index which contains all other non global indexes.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # setup tooling environment
    env = env_manager.get_environment(env_name)
    if env is None:
        raise ValueError("Inappropriate environment name provided")

    auth = get_auth(region=env.aws_region)

    global_index = Indexes.GLOBAL
    global_index_name = INDEX_MAP[global_index]

    others: List[str] = []

    for index in Indexes:
        if index != global_index:
            others.append(INDEX_MAP[index])

    endpoint = f"{env.search_service_endpoint}/_aliases"

    # see https://opensearch.org/docs/1.3/opensearch/index-alias/
    method = HTTPMethods.POST
    payload = {
        "actions": [
            {
                "add": {
                    "index": index_name,
                    "alias": global_index_name
                }
            }
            for index_name in others
        ]
    }

    response = requests.request(
        method=method.value,
        url=endpoint,
        json=payload,
        auth=auth
    )

    try:
        response.raise_for_status()
        try:
            print(response.json())
        except:
            print(response)
    except requests.exceptions.HTTPError as he:
        print(f"Error occurred: {he}.")


@app.command()
def create_body_field_ngram_registry_index(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    index_name_override: Optional[str] = typer.Option(
        None,
        help=f"If the name of the index is not the default registry, can provide an override."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Setups up the special ngram registry index
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    if env is None:
        raise ValueError("Inappropriate environment name provided")

    auth = get_auth(region=env.aws_region)

    registry_index = Indexes.REGISTRY
    registry_index_name = INDEX_MAP[registry_index]
    endpoint = f"{env.search_service_endpoint}/{index_name_override or registry_index_name}"

    # see https://opensearch.org/docs/latest/search-plugins/searching-data/autocomplete/
    method = HTTPMethods.PUT
    payload = {
        "mappings": {
            "properties": {
                LINEARISED_FIELD: {
                    "type": "text",
                    "analyzer": "autocomplete"
                }
            }
        },
        "settings": {
            "analysis": {
                "filter": {
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20
                    }
                },
                "analyzer": {
                    "autocomplete": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "edge_ngram_filter"]
                    }
                }
            }
        }
    }

    response = requests.request(
        method=method.value,
        url=endpoint,
        json=payload,
        auth=auth
    )

    print(response.text)

    try:
        response.raise_for_status()
        try:
            print(response.json())
        except:
            print(response)
    except requests.exceptions.HTTPError as he:
        print(f"Error occurred: {he}.")


@app.command()
def describe_global_alias_index(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Creates a global alias index which contains all other non global indexes.
    """
    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    auth = get_auth(region=env.aws_region)

    global_index = Indexes.GLOBAL
    global_index_name = INDEX_MAP[global_index]

    endpoint = f"{env.search_service_endpoint}/_alias/{global_index_name}"

    # see https://opensearch.org/docs/1.3/opensearch/index-alias/
    method = HTTPMethods.GET

    response = requests.request(
        method=method.value,
        url=endpoint,
        auth=auth
    )

    try:
        response.raise_for_status()
        try:
            print(response.json())
        except:
            print(response)
    except requests.exceptions.HTTPError as he:
        print(f"Error occurred: {he}.")


if __name__ == "__main__":
    app()
