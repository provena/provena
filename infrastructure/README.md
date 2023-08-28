# Provena CDK infrastructure

## Infrastructure and CDK Overview

A core part of the Provena application is configured in the included CDK application.

This CDK app defines an extensive configurable interface into the Provena application and is designed to be customisable to meet the requirements of your deployment.

The [CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) is "a framework for defining cloud infrastructure in code and provisioning it through AWS CloudFormation". There is a wealth of documentation available online about the tool, so we will focus on the critical parts relevant to this application below.

The Provena CDK app deploys the following components:

-   A VPC and various public and private subnets - used to manage access to and connections between the VPC enabled components (ECS containers, load balancers and RDS instance)
-   A Keycloak Container running as a single node ECS cluster fronted by an application load balancer performing SSL termination (no clustering enabled currently) - primary authentication and authorisation mechanism for Provena - includes configuration to broker AWS credentials dynamically and connects to various external IdPs
-   An RDS PostgreSQL instance either from scratch or from an existing snapshot which backs and persists the Keycloak deployment
-   A set of Route53 DNS records against a custom domain (hosted zone) - used to map the various system endpoints to the desired customisable domain names
-   A Neo4j Graph database instance running in community edition in a docker container persisted through a mounted EFS volume deployed in an ECS cluster - single node (no clustering enabled currently) - used to persist the PROV-O provenance data ingested from the Prov API
-   A set of Docker container deployed Lambda functions for the core system APIs - serverless, including
    -   Identity Service API (handle ARDC proxy) - mints and manages ARDC handles
    -   Auth API (and associated DynamoDB tables for persistence) - assists in resource level authorisation and helper mechanisms for dynamic authorisation resolution
    -   Search API (proxy for AWS Open Search registry index) - acts as a Provena compatible authorisation and query proxy into the AWS open search cluster indexing the registry
    -   Registry API (and associated DynamoDB tables for persistence) - manages a central repository of identified resources in Provena
    -   Data Store API - allows dataset registration and manages credential brokering with AWS
    -   Provenance Store API - handles the registration of provenance activites including PROV-O conversion and lodging into the graph database
-   A job dispatching SQS queue workflow for managing batch submissions of Provenance model runs (from the Prov API)
-   Assorted utility basic Python lambda functions, such as:
    -   Lambda Warmer which runs a root HTTP request to all core APIs to prewarm them in the UI
    -   Search streamer which indexes the OpenSearch cluster from the registry DynamoDB table
-   A set of CloudFront static websites against custom domains, including
    -   Landing Portal - Provena front page and access gateway
    -   Registry - User front end to the Registry API functionality
    -   Data Store - User front end to the Data Store API functionality
    -   Provenance Store - Enables provenance graph visualisation, exploration and bulk model run registration
-   An AWS OpenSearch single node cluster (configurable) which indexes the contents of the Registry table through an event driven lambda indexing function
-   An AWS Backup Vault and associated backup plans/rules for critical resources (configurable policies)

This deployment is managed through a CodePipeline Pipeline and associated CodeBuild jobs - this includes:

-   a self mutation workflow to enable synchronisation of the CDK pipeline description with the deployed pipeline (see [here](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html) for more about the opinionated CDK Pipelines library)
-   configurable set of unit, integration, type (mypy, typescript) and system tests which run in pipeline pre and post deployment
-   three pipelines:
    -   full build/test/deploy pipeline
    -   ui build only pipeline (builds UIs and updates deployment)
    -   interface pipeline (which runs the Pydantic -> TS interface export and self updates the repository if changes are made)

See below for more information about how to deploy the Provena application.

## Installing Dependencies

Assure you are working in this folder for the below steps. The below steps are for linux - it's possible to synth on Windows but it is untested at this stage.

### CDK and Node setup

Ensure you have a global node cdk installation which is up to
date.

I recommend using [nvm](https://github.com/nvm-sh/nvm) to manage the node
versions.

Follow the above instructions to install nvm, then

```
nvm install 20
nvm use 20
```

Check the requirements.txt file for the current CDK version of this project `aws-cdk-lib` - and install it below at the matching version e.g.

```
npm install -g aws-cdk@2.81.0
```

Check your CDK version with `cdk --version` - it should match the python `aws-cdk-lib` version in `requirements.txt`.

### Docker Setup

In general, local asset bundling is preferred (see [here](https://docs.aws.amazon.com/cdk/api/v1/docs/aws-s3-assets-readme.html#asset-bundling)). However, if this fails, CDK will fall through to performing Docker bundling.

Additionally, if you try to synthesise and deploy the whole application (rather than the Pipeline Stack), Docker is required (as the Lambda APIs use Docker assets).

Therefore, it is recommended to have a local rootless Docker setup.

See [here](https://docs.docker.com/engine/security/rootless/) for guidance on setting up a rootless Docker environment.

### Python virtual environment

Setup a virtual environment:

```
python3.10 -m venv .venv
source .venv/bin/activate
```

Install minimum required for deployment:

```
pip install -r requirements.txt
```

and for development:

```
pip install -r requirements-dev.txt
```

### AWS Deployment permissions

You need to ensure two things

1. You have AWS credentials currently activated which allow IAMPowerUser permissions into your target deployment account
2. You have bootstrapped the target AWS account using the [CDK bootstrapping process](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)

If this is not configured correctly, deployment will fail.

As an additional failsafe, in the configuration below, we will manually specify target accounts which will prevent accidental deployment into the incorrect AWS environment due to unintended incorrect account credentials.

## A note about the Provena pipelines

The way that CodePipeline works is different to something like Github Actions. Instead of defining a declarative pipeline file in your repository which is run on some set of git events, CodePipeline is a deployed resource in an AWS account which has a state with a separate lifecycle to your repository code.

CDK Pipelines is an opionionated, high level, CDK construct which is designed to make deploying a CodePipeline CI/CD deployed CDK application simple.

It includes the capacity for a CodePipeline pipeline to update itself. A process known as "self mutation". The mechanism is as follows:

-   We define a CDK application which defines a Stack
-   This stack includes a CodePipeline pipeline
-   This pipeline does the following:
    -   pulls the repo source code
    -   synthesises the application
    -   self mutates - i.e. runs a deploy of the synthesised pipeline stack against itself - updating itself if required
    -   either continues, or shuts down and restarts in the updated version
    -   builds any application assets
    -   runs pre deployment steps (type checks, unit tests etc)
    -   deploys the Provena application stack
    -   runs post deployment steps (integration tests, system test, ui builds etc)

Therefore, we define two concepts in the following notes:

-   the Pipeline stack: this is the stack which deploys the CodePipeline pipeline
-   the Application stack: this is the stack which is deployed **by** the Pipeline stack's CodePipeline - i.e. the Provena application

The shorthand "pipeline" and "app" are used in the helper functions below.

## Configuring your Provena Deployment

The Provena application has a mixture of

-   required existing resources in the AWS account e.g. AWS Secret Manager credentials, DNS certificates, Hosted Zones etc
-   deployment and application configuration e.g. Git repo/branch, instance sizes etc

For this reason, we provide a rich configuration interface into the application.

Below, we will provide an overview of some of the key concepts for managing Provena configuration and interacting with your deployed application.

**We recommend that new users, who want to deploy Provena, visit the more thorough deployment guide available here: [Provena from Scratch](https://confluence.csiro.au/display/RRAPIS/HOW+TO+Deploy+Provena+from+SCRATCH).**

### How is config managed in Provena?

The Provena application cannot be deployed without a minimum set of existing resources.

Provena has a workflow to manage configuration.

In the `configs` folder you will see two files:

-   `config_map.py`
-   `template_custom_deployment.py`

The config map defines a mapping from a config ID to a function which generates a `ProvenaConfig` object.

The `template_custom_deployment` provides a scaffold to get started with your Provena application config.

It is worth noting that all of the commands mentioned in 'Deploying and managing Provena' relate to a specific Config ID - so choose a helpful short hand for your application.

## Deploying and managing Provena

**We recommend that new users, who want to deploy Provena, visit the more thorough deployment guide available here: [Provena from Scratch](https://confluence.csiro.au/display/RRAPIS/HOW+TO+Deploy+Provena+from+SCRATCH).**

The below steps assume that you have a defined Config ID which is setup as above. The commands will refer to the config ID as <config_id>.

### How do we run CDK commands

CDK includes a rich CLI which helps to deploy, update and diff applications. However, by default, we can only define a single app target - normally `app.py`. Due to Provena's deployment requirements, we have multiple CDK app files.

The CLI tool enables the specification of a cdk file (`--app`) and and output cdk synth path (`--output`). These are customised as part of the config process.

We have defined a helper [typer cli](https://typer.tiangolo.com/typer-cli/) script which:

-   looks up the config id from the config map
-   generates the config with the specified generator function
-   reads the cdk app file, output path, and stack names
-   generates a customised cdk command which has the required arguments and stack names, and includes the user's commands

### Using the app_run.py helper script

Ensure you have installed all the dependencies, as mentioned above, then run

```
python app_run.py --help
```

Typer CLIs generate a nice help interface so you will see a set of available options.

In our case, there are three main arguments:

-   `CONFIG_ID` - the config id mentioned above - this is essentially specifying the target Provena deployment that you want to run actions against
-   `RUN_TARGET` - this allows you specify whether you want to run cdk commands against the Pipeline Stack, or the deployed Application Stack
-   `COMMANDS` - everything included after will be passed through to the cdk cli command

For example, if I want to compare the application stack against the deployed application:

```
python app_run.py <config_id> app diff
```

This will result in a command with the following structure

```
cdk --app "python provena_app.py" --output "<config_id>_cdk.out" diff <variable>Pipeline/deploy/<variable>
```

Where some values have been omitted above.

Using this approach means you can manage multiple Provena applications which have separately defined and managed configurations through a single CDK cli proxy interface.
