# README

# Auth API

The Provena Auth API provides a set of user and admin tools which assists with:

-   creating, viewing and managing system access requests
-   generating access reports which assess the current users access to the components configured in the system Authorisation Model
-   creating, querying and managing user groups
-   managing the User to Registry Person Link

The Auth API is used heavily by other APIs as it communicates with the User groups table to enable querying of group membership. This group information is used to enforce resource level permissions on registry items.

# Local deployment

## Setup Prerequisites

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

Unit tests can be run in a mocked environment by using pytest. First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

`pip install -r testing_requirements.txt`

Then run pytest,

`pytest`

Tests can also be done in a VSCode environment also by using the Testing UI extension.

All tests will setup a mock environment to test functionality in these areas:

-   Authorization in `test_authorization.py`
-   Core auth functionality in `test_functionality.py` and others.

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
