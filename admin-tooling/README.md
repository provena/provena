# Admin Tooling

This folder contains a set of admin tools which can help manage and administrate a Provena deployment.

There are a few key steps to using the tools, described below.

## Installation

You need to work inside the corresponding folder's tool.

E.g. to use the registry admin tools

```
cd registry
```

Then setup a python virtual environment (3.10 recommended)

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

All of the tools use Typer CLIs - you can execute the corresponding script using

```
python script_name.py
```

To get help, use `--help`. Some scripts have subcommands. You can also use
`--help` on these sub commands.

## Managing environments

The tooling environment manager is a python package which handles customising the targeted Provena deployment.

A Provena deployment exposes a set of API endpoints which depend on the base domain name.

In the below examples and Schema, note that the "name" field is the environment name parameter which is required in most of the admin tooling CLI functions.

### Schema

The environments.json file must satisfy the `ToolingEnvironmentsFile` Pydantic schema below:

```
class ToolingEnvironment(BaseModel):
    # Core values

    # What is the name of this environment?
    name: str
    # What is the Provena application stage?
    stage: str
    # What is the base domain e.g. dev.rrap-is.com
    domain: str
    # What is the auth realm name?
    realm_name: str

    # In the specified overrides - are there any variables to replace? Specify
    # the key (in CLI) and the in text value to find/replace
    replacements: List[ReplacementField] = []

    # Overrides

    # Endpoints are auto generated but can be overrided

    # APIs
    datastore_api_endpoint_override: Optional[str]
    auth_api_endpoint_override: Optional[str]
    registry_api_endpoint_override: Optional[str]
    prov_api_endpoint_override: Optional[str]
    search_api_endpoint_override: Optional[str]
    search_service_endpoint_override: Optional[str]
    handle_service_api_endpoint_override: Optional[str]

    # Keycloak
    keycloak_endpoint_override: Optional[str]

    # Defaults - overridable
    aws_region: str = "ap-southeast-2"

class ToolingEnvironmentsFile(BaseModel):
    envs: List[ToolingEnvironment]
```

### Basic case

In the basic case, you should add an entry for your Provena deployment like so:

```
{
    "envs": [
        {
            "name": "MyProvena",
            "stage": "PROD",
            "domain": "provena.yourdomain.io",
            "realm_name": "TODO"
        }
    ]
}
```

This is the minimum viable environment to target.

-   name: The user defined name of the target - keep it short but easy to remember - not used anywhere else
-   stage: The application stage - e.g. DEV, STAGE, PROD
-   domain: The base domain of the provena deployment- this is postfixed onto the standard set of API endpoints
-   realm_name: The keycloak authorisation server realm name

### Advanced case

In the RRAP IS team, we use a process we call the "feature deployment" workflow. This means we spin up sandbox Provena instances for feature development. In these cases, the API endpoints have a special prefix depending on a number specific to our process. Let's call this number the 'feature_number'. The environment file structure is capable of handling in-situ replacements which are fed via parameters from the CLI tooling.

E.g. consider this feature branch workflow environment file

```
{
    "envs":[
        {
            "name": "feature",
            "stage": "DEV",
            "domain": "dev.rrap-is.com",
            "realm_name": "rrap",
            "replacements": [
                {
                    "id": "feature_number",
                    "key": "${feature_number}"
                }
            ],
            "datastore_api_endpoint_override": "https://f${feature_number}-data-api.dev.rrap-is.com",
            "auth_api_endpoint_override": "https://f${feature_number}-auth-api.dev.rrap-is.com",
            "registry_api_endpoint_override": "https://f${feature_number}-registry-api.dev.rrap-is.com",
            "prov_api_endpoint_override": "https://f${feature_number}-prov-api.dev.rrap-is.com",
            "search_api_endpoint_override": "https://f${feature_number}-search.dev.rrap-is.com"
        }
    ]
}
```

Note that we define an id and key for the feature number replacement. The id is the CLI input key. The Key is the value which will be replaced in the API endpoint overrides.

When we use the CLI tools - all the endpoints feature a `param` option which can be used multiple times, they have a specific syntax

```
python script.py sub_command argument1 argument2 --param id1:value1 --param id2:value2
```

For our feature deployment workflow, we can perform the replacement like so:

```
python environment_bootstrapper.py bootstrap-stage feature --suppress-warnings --param feature_number:${ticket_no}
```

where `ticket_no` is passed from the environment.
