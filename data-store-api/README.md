# README

# Data Store API

The Provena Data Store API facilitates the registration of datasets in the Provena Registry. 

The Data Store API, in conjunction with other system APIs, supports the functionality of the Data Store UI. 

The Data Store API acts as a proxy to the underlying storage layer to provide a simple unified Provena authorisation interface for data access. 

This critical registration workflow is summarised below:

1. Data store API, upon request, delivers a JSON Schema specification for the required data set metadata
1. The data store UI displays this form based on the schema
1. User provides a set of valid dataset metadata and requests a new dataset
2. Data store API seeds a new dataset in the Registry (using it's Keycloak service account credentials), returning the minted system identifier
3. A new location is created within the storage s3 bucket with a folder path based on the system identifier
4. A file is placed into this location which contains the dataset metadata as a JSON file 
5. The dataset is updated with the complete metadata including the s3 storage path

The data storage access is managed through a Keycloak facilitated OIDC identity provider trust relationship (the AWS account is configured within CDK to trust the Keycloak IdP deployed in the Provena application). This trusted client ID can only be assumed by the data store API keycloak service account. 

Critical data access workflow

1. User requests r/w credentials for a dataset by ID
2. Data store API uses the auth API and registry API to validate access permissions for the resource
3. Data store API assumes the keycloak service role associated with the AWS OIDC IdP
4. Data store API uses AWS sts to generate temporary credentials against a customised policy document which restricts access to the specified S3 subpath (with specified actions) - access is granted through the WebIdentityToken sts delivery mechanism 
5. Data store API returns these credentials, and optionally a presigned console URL which is deeplinked into the specified location in the s3 bucket

It is worth noting that the OIDC role is scoped to the storage bucket meaning that in the worst case of cred leaks, the S3 bucket is the permission boundary.

# Local deployment

## Setup Prerequisites
- virtual environment setup
- environment file setup

### Virtual Environment Setup
To set up a virtual environment for deploying the API, run the following commands in the directory of the API (same directory as this readme)

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Additionally, for development and testing, install the testing requirements:

```pip install -r testing_requirements.txt```

 **Note**: You may need to manually export the `AWS_DEFAULT_REGION` env variable if you use a .env file. This only applies for running the API, not for testing, in which this is set automatically. (E.g., Use `export AWS_DEFAULT_REGION=ap-southeast-2` for linux terminals)

### Environment File Setup / Choosing a deployed Provena Application to bootstrap from
This repo contains bootstrap tooling for automatically delivering environment files to api directories given a desired deployment to target (e.g., Prod, Dev, Feature).

1. Checkout to the branch whose API you wish to locally deploy.
2. Navigate to /admin-tooling/environment-bootstrapper. This is where the environment bootstrapper tooling is located.
3. See the readme in that directory for further instructions on using the bootstrapping tooling to deliver a .env file.

**Note**: If you are running the API against deployed AWS resources, you need to have the correct AWS credentials activated in your environment. You may need to generate temporary credentials for, or login to, the target AWS account if your are not developing in an AWS service account enabled environment (such as an EC2 instance).

## Running the API
Once the virtual environment is setup and the environment file is ready, run the following command to start the API:

```./start_server.sh```

You may alter the default port by passing in the following arguments or editing them in the start_server.sh script:

```./start_server.sh --port <port>```

# Testing
## Automated Unit Tests
Unit tests can be run in a mocked environment by using pytest. First, ensure you have a python virtual environment setup (e.g. .venv) as per the steps above. Then, install the test requirements by running the following command:

```pip install -r testing_requirements.txt```

Then run pytest,

```pytest```

Tests can also be done in a VSCode environment also by using the Testing UI extension.


All tests will setup a mock environment to test functionality in these areas:
- Authorization in `test_authorization.py`
- Core datastore functionality in  `test_functionality.py` and others.

## Thunderclient
Thunderclient is a VSCode extension that allows for the creation of HTTP requests and the viewing of responses. It is useful for testing the API manually as iterative changes are made. Some APIs in the repo have simple default requests already. See the next section on API documentation for help discovering the required endpoint payloads and methods. To use thunderclient, install the thunder client extension then enable the setting in the json settings UI which saves collection to the workspace. If you refresh the thunder client panel it should pick up the collection and requests.

# API Documentation
API Documentation can be viewed at *endpoint*/docs or *endpoint*/redoc.