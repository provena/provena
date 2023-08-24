# README

# Job API

The Provena Job API is an API consumed by other system services and users to launch and monitor asynchronous system tasks.

Only admins of the service (and therefore other API service accounts) can launch jobs.

Users can view information about tasks they own, at an individual and batch level.

Admins can view information about anyone's tasks at the individual or batch level.

## Task Launching

The Job API is a simple service. When launching a task, it validates the payloads according to the job sub type's payload model, then publises to the specific SNS topic for that job type. This causes a notification fan out into a status table (through a lambda connector), a SQS queue, and a ECS invoker lambda function.

## Task Monitoring

Task monitoring is achieved by pulling items from a DynamoDB table.

The table is indexed by 1) session ID 2) username/timestamp 3) batch id/timestamp.

This allows three fetch views 1) specific session ID, 2) by username (ordered by timestamp) 3) by batch ID (ordered by timestamp).

UI clients are encouraged to poll this API as long as the task isn't in a completed state (which would be wasteful).

All listing endpoints are paginated.

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

First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

`pip install -r testing_requirements.txt`

Then run pytest,

`pytest`

Tests can also be done in a VSCode environment also by using the Testing UI extension.

All tests will setup a mock environment to test functionality in these areas:

-   Authorization in `test_authorization.py`
-   Core Provenance functionality in `test_functionality.py` and others.

## Thunderclient

Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation

API Documentation can be viewed at _endpoint_/docs or _endpoint_/redoc.
