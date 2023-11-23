# Identity Service API

The Provena Information System Identity Service API is a Python FastAPI wrapper of the [ARDC Handle Service](https://ardc.edu.au/services/ardc-identifier-services/ardc-handle-service/).

The ARDC handle service allows the minting and management of persistent web identifiers which resolve to a configurable domain/endpoint.

This API is used heavily throughout the Provena infrastructure to mint and update identifiers.

This API exposes most of the key ARDC handle functions in a fully typed Pydantic/OpenAPI compatible API.

This includes

-   mint (creates a new Handle identifier)
-   add value (adds a value of a specified type to the handle)
-   add value by index (adds a value of specified type at specified index)
-   get (fetches values associated with a handle)
-   list (lists all the handles on the given domain)
-   modify by index (modifies an existing value by index)
-   remove by index (removes an existing value by index)

Below, the process of bootstrapping a set of environment variables is specified. In the identity service, it is important to correctly specify the `handle_service_endpoint` and `handle_service_creds`. The endpoint should match the credentials - i.e. the testing endpoint (https://demo.identifiers.ardc.edu.au/pids/) should be used when using testing credentials, and the production endpoint (https://identifiers.ardc.edu.au/pids)

# Local deployment

## Setup Preqrequisites

-   virtual environment setup
-   environment file setup

### Virtual Environment Setup

To set up a virtual environment for deploying the API, run the following commands in the directory of the API (same directory as this readme)

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Additionally, for development and testing, install the testing requirements:

`pip install -r testing_requirements.txt`

**Note**: You may need to manually export the `AWS_DEFAULT_REGION` env variable if you use a .env file. This only applies for running the API, not for testing, in which this is set automatically. (E.g., Use `export AWS_DEFAULT_REGION=ap-southeast-2` for linux terminals)

### Environment File Setup / Choosing a deployed Provena Application to bootstrap from

This repo contains bootstrap tooling for automatically delivering environment files to api directories given a desired deployment to target (e.g., Prod, Dev, Feature).

1. Checkout to the branch whose API you wish to locally deploy.
2. Navigate to /admin-tooling/environment-bootstrapper. This is where the environment bootstrapper tooling is located.
3. See the readme in that directory for further instructions on using the bootstrapping tooling to deliver a .env file.

**Note**: If you are running the API against deployed AWS resources, you need to have the correct AWS credentials activated in your environment. You may need to generate temporary credentials for, or login to, the target AWS account if your are not developing in an AWS service account enabled environment (such as an EC2 instance).

## Running the API

Once the virtual environment is setup and the environment file is ready, run the following command to start the API:

`./start_server.sh`

You may alter the default port by passing in the following arguments or editing them in the start_server.sh script:

`./start_server.sh --port <port>`

# Testing

## Automated Unit Tests

Note: the identity service will create a handle during testing. We recommend using a set of testing credentials if you want to run the unit tests for the id service.

Unit tests can be run in a mocked environment by using pytest. First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

`pip install -r testing_requirements.txt`

Then run pytest,

`pytest`

Tests can also be done in a VSCode environment also by using the Testing UI extension.

All tests will setup a mock environment to test functionality in these areas:

-   Authorization in `test_authorization.py`
-   Core id-service functionality in `test_functionality.py` and others.

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
