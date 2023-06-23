# README

# Registry API

The Provena Registry API enables users to register, update, explore and share persistently identified resources.

The Registry is a critical part of Provena as it facilitates the creation of and linking between persistently identified artefacts of provenance, such as people, organisations, models and model runs.

The Registry API implements the required back-end functionality to support the Registry web application. See below to deploy and test the Registry API locally.

# Design Principles

The Registry API has been designed to balance modularity/extensibility (quickly being able to add new Registry sub types) and robustness/clarity (well typed interfaces and consistent behaviour).

This was achieved through the dynamic generation of subroutes based on:

-   a set of required Pydantic models for each subtype
-   configuration of subtype routes based on desired behavioural overrides

These models are defined in the repo's `SharedInterfaces` python package and are configured in the `RegistrySharedFunctionality` python package and the `main.py` file in this folder.

The core of the Registry API is the `item_type_route_generator.py` in `helpers`. This file handles the creation of the routes based on the route config and other options.

## Subtype Actions

Each subtype exposes the following actions (though some actions are disabled or changed for particular subtypes)

-   fetch - fetches the item by id
-   list - lists items of this type with optional filtering/ordering
-   seed - creates an incomplete 'seed' version of this item subtype - used to enable handle generation without a complete payload
-   update - updates the DomainInfo (metadata) of an existing registry item - can update a seed item to a complete item
-   revert - reverts the metadata to a previous historical version
-   create - creates a new item of this type
-   schema - fetches the JSON schema description of the required metadata
-   ui_schema - fetches the [RJSF](https://github.com/rjsf-team/react-jsonschema-form) specific ui schema which is used for rendering in the Registry UI
-   validate - validates the metadata payload without registration
-   auth/evaluate - evalues the user's available/granted roles against this resource
-   auth/configuration - gets the authorisation settings for this item
-   auth/roles - gets the available roles for this subtype
-   locks/lock - locks the resource
-   locks/unlock - unlocks the resource
-   locks/history - gets the history of lock/unlock actions
-   locks/locked - checks if the resource is locked

## Subtype Options

There are some opportunities for configuration of the generated subtype routes

-   visibility - should this route be shown in the auto docs?
-   accessibility - should this route require special keycloak roles (e.g. service account roles?)
-   routes - which routes should be available (e.g. proxy routes, see below)

## Proxy Routes

In some cases, it is inappropriate for a user to directly create/update etc items of a particular subtype. Key examples are datasets and model runs. Datasets cannot be registered directly because they have a tied in lifecycle with a data store S3 storage location. Model runs must be transformed and lodged by the Prov API.

The Registry API has been setup to facilitate these inter API requirements through two mechanisms

-   special per route role limitations
-   proxy routes

Role route limitations means we can enforce only specific Keycloak roles for particular actions - e.g. only the Data Store API service account can create/update/seed datasets.

Proxy routes (such as proxy update, proxy create) etc, are also generally role limited to APIs, and enables the requesting party to request that the action be taken _as if_ the user was actually a different user (specified by username). For example, the proxy create action allows the Data Store API to mint a dataset which is owned by a real non service account system user - meaning they can administer the item as if they created it.

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
-   Core registry functionality in `test_functionality.py`

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
