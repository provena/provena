# README

# Provenance API

The Provena Provenance API enables the registration of workflow provenance records according to the Provena workflow provenance data models. The Provena data model represents modelling as activites which consume inputs, produce outputs, at a particular point in time, associated with People and Organisations in the Registry.

There are two primary registration mechanisms:

-   individual record registration (using the Pydantic models directly)
-   CSV bulk model run record ingestion (using a job queue workflow deployed separately)

The primary mechanism of registration through the Prov API is the conversion of Provena provenance into a standard [PROV-O](https://www.w3.org/TR/prov-o/) representation.

Once this conversion is complete, a modified version of [prov-db-connector](https://github.com/DLR-SC/prov-db-connector) is used to lodge these prov-o documents into a graph database, in this case Neo4j.

Once lodged, the Prov API provides querying capability (proxying simple [Cypher](<https://en.wikipedia.org/wiki/Cypher_(query_language)>) queries into the neo4j database). This currently includes an upstream and downstream query.

Workflow provenance can support transparency of the modelling activities and facilitate repetition of the knowledge generation activity. Provenance can also assist in determining the integrity of certain knowledge and knowledge generation activities where important decisions are based off of this knowledge.

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

This set of tests requires **docker** and **docker compose** to be setup and runnable from the docker and docker-compose commands. I wouldn't recommend running pytest in sudo mode meaning that your docker install should be configured for your user or as a rootless install (which I recommend).

The reason for this is that the prov API is heavily dependent on the graph database backend for querying, storing etc. Testing without a workable backend would be difficult and potentially not very useful. Neo4j is spun up as a pytest fixture using the pytest-docker package. This dynamically injects the endpoint/port of this server into the app for testing.

Currently, all neo4j interactions are real (docker backend) while other API interactions like data store/registry are mocked using `monkeypatch`.

Assuming docker/docker-compose is setup, unit tests can be run in a mocked environment by using pytest. First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

`pip install -r testing_requirements.txt`

Then run pytest,

`pytest`

Tests can also be done in a VSCode environment also by using the Testing UI extension.

All tests will setup a mock environment to test functionality in these areas:

-   Authorization in `test_authorization.py`
-   Core Provenance functionality in `test_functionality.py` and others.

### Cleaning up failed or debugged tests

Sometimes after a test fails or is debugged, the pytest-docker doesn't get the chance to tear down the infra. You will see this exhibited as a 'port already in use' error when trying to run the tests.

You can fix this by running `docker ps` to find the neo4j container, then `docker stop <container id>` and `docker rm <container id>`. This will remove the running container so that the pytest fixture can spin it up properly.

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
