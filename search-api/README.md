# README

# Search API

The Search API acts as a Provena Keycloak authenticated proxy to an AWS OpenSearch cluster which indexes the Provena Registry items.

The Search API uses its AWS service role when deployed to create AWS V4 signed credentials which allows for HTTPS requests against the search cluster. The user must therefore possess appropriate local AWS credentials when locally testing this API, as mentioned below.

The Provena Registry is kept in sync with the OpenSearch index through an event driven Lambda function - the details of this implementation are available in the CDK source code.

The OpenSearch cluster is configured with a fuzzy and n-gram enabled index. The set of indexable fields is configured within the Pydantic class Schemas on a per model basis. 

This API exposes a simple registry search endpoint. It enables searching based on a string query, and optionally can filter the results by subtype. This filtration is at the index search level (not a post process). 

The results include the strength of the match (a score) and the ID of the matching item - ordered in descending strength. The limit is set to 10 by default. 

Because only the ID, not the payload, of the item is returned, the registry API is the single point of authorisation protection for resource level registry item permissions. The user must take the subsequent action of fetching the item.

The Search API is used across many of the Provena UIs as a simple way to search for registered items.

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

**Note**: You may need to manually export the `AWS_DEFAULT_REGION` env variable if you use a .env file. This only applies for running the API, not for testing, in which this is set automatically. (E.g., Use `export AWS_DEFAULT_REGION=ap-southeast-2` for linux terminals)

# Testing

## Automated Unit Tests

Unit tests can be run in a mocked environment by using pytest. First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

`pip install -r testing_requirements.txt`

Then run pytest,

`pytest`

Tests can also be done in a VSCode environment also by using the Testing UI extension.

All tests will setup a mock environment to test functionality in these areas:

-   Authorization in `test_authorization.py`
-   Core search functionality in `test_functionality.py`

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
