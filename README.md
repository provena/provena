# Provena

Provena is an information system built to capture, manage, and analyse [Provenance](https://ardc.edu.au/resource/data-provenance) records, and their artefacts. Provena additionally implements a robust data storage solution for seamless interaction with and inspection of the data referenced in provenance records.

## Description

To facilitate system functionality, Provena implements a suite of components. Each comprise of a Docker deployed Python FastAPI serverless microservice, and where user interaction is required, these APIs are paired with a front-end web application. The following components are implemented:

## Citations

### Conference paper

Yu, J., Baker, P., Cox, S.J.D., Petridis, R., Freebairn, A.C., Mirza, F., Thomas, L., Tickell, S., Lemon, D. and Rezvani, M., Provena: A provenance system for large distributed modelling and simulation workflows, In Vaze, J., Chilcott, C., Hutley, L. and Cuddy, S.M. (eds) MODSIM2023, 25th International Congress on Modelling and Simulation. Modelling and Simulation Society of Australia and New Zealand, July 2023, pp. 14–20. ISBN: 978-0-9872143-0-0. https://doi.org/10.36334/modsim.2023.yu90

### Software citation

Yu, Jonathan; Baker, Peter; Petridis, Ross; Freebairn, Andrew; Thomas, Linda; Mirza, Fareed; Tickell, Sharon; Lemon, David; Rezvani, Mojtaba; Hou, Xinyu; Cox, Simon (2023): Provena. v1. CSIRO. Software Collection. https://doi.org/10.25919/1edm-0612

See also https://data.csiro.au/collection/csiro:59335

### Brief Description of Components

**Identity Service (API)**

The Identity Service is a heavily utilised component of the Provena IS. It provides the critical functionality of the minting and management of persistent web identifiers which resolve to a configurable domain/endpoint. It is implemented as a Python FastAPI wrapper of the [ARDC Handle Service](https://ardc.edu.au/services/ardc-identifier-services/ardc-handle-service/).

For more info on the Identity Service API:  
[Identity Service API Readme](./identity-service/README.md)

**Registry (API and UI)**

The Provena Registry facilitates the registration of resources in the Provena Registry. Specifically, it enables the registration, updating, management, and exploration of persistently identified resources, such as people, organisations, models, and more.

The Provena Registry UI is a Typescript React GUI which enables user friendly interaction with the Provena Registry API.

For more info on the Provena Registry API and UI:  
[Registry API Readme](./registry-api/README.md)  
[Registry UI Readme](./registry-ui/README.md)

**Data Store (API and UI)**  
The Provena Data Store API facilitates the registration of dataset entities and storage of datasets in the Provena Registry and AWS S3 data storage, respectively. It is the datasets which form the major inputs and outputs of workflow provenance recorded in the Provena Provenance Store. The Data Store API acts as a proxy to the underlying storage layer to provide a simple unified Provena authorisation interface for data access.

The Provena Data Store UI is a Typescript React GUI which enables user friendly interaction with the Provena Data Store API.

For more info on the Provena Data Store API and UI:  
[Data Store API Readme](./data-store-api/README.md)  
[Data Store UI Readme](./data-store-ui/README.md)

**Provenance Store (API and UI)**

The Provena Provenance API enables the registration of workflow provenance records according to the Provena workflow provenance data models. The Provena data model represents modelling as activities which consume inputs, produce outputs, at a particular point in time, associated with People and Organisations in the Registry.

There are two primary registration mechanisms:

- individual record registration (using the Pydantic models directly)
- CSV bulk model run record ingestion (using a job queue workflow deployed separately)

Workflow provenance can support transparency of the modelling activities and facilitate repetition of the knowledge generation activity. Provenance can also assist in determining the integrity of certain knowledge and knowledge generation activities where important decisions are based off of this knowledge.

The Provena Provenance Store UI is a Typescript React GUI which enables user friendly interaction with the Provena Provenance API and Registry API.

This UI facilitates

- interactive visualisation of provenance graphs
- tooling to assist with bulk registration of provenance model run activities

and more...

For more info on the Provena Provenance API and UI:  
[Provenance API Readme](./prov-api/README.md)  
[Provenance UI Readme](./prov-ui/README.md)

**Authorisation Service (API)**

The Provena Auth API provides a set of user and admin tools which assists with:

- creating, viewing and managing system access requests
- generating access reports which assess the current users access to the components configured in the system Authorisation Model
- creating, querying and managing user groups
- managing the User to Registry Person Link

The Auth API is used heavily by other APIs as it communicates with the User groups table to enable querying of group membership. This group information is used to enforce resource level permissions on registry items.

For more info on the Authentication API:  
[Authentication API Readme](./auth-api/README.md)

**Search Service (API)**

This API exposes a registry search endpoint which queries an Elastic Search index of the Registry.

The Search API is used across many of the Provena UIs as a simple way to search for registered items.

For more info on the Search API:  
[Search API Readme](./search-api/README.md)

## Technologies Used

Please visit the READMEs of the respective compoents for information on the technologies in each component. Links are included in component descriptions above.

## Getting Started

### Deploying and managing Provena

**We recommend that new users, who want to deploy Provena, visit our thorough deployment guide available here: [Provena from Scratch](https://confluence.csiro.au/display/RRAPIS/HOW+TO+Deploy+Provena+from+SCRATCH).**

### Deploying APIs and UIs

Once a Provena deployment has been configured and deployed as per the above guide, individual APIs and UIs can be deployed for development, debugging or testing purposes by following instructions in their respective READMEs.

## Usage

Provena comes with a suite of fully developed User Interface web pages that facilitate a user friendly interaction with the Provena APIs and resources.

Additionally, all Provena services can be accessed by authorised users through the system APIs. Provena has well documented REST APIs (see API endpoint documentation in READMEs) which can be interacted with directly using a REST client such as Postman or thunderclient, or programmatically using Python, for example. Programmatic interactions are recommended for our power users and we have guide on authentication for this. See our API access docs: [API access docs](http://docs.provena.io/API-access/).

## Testing

## Component Unit tests

Each API component has a dedicated unit test suite. Unlike the Integration tests which are purposed for testing user stories and interacts between multiple APIs at once, the unit test were designed to test individual endpoints and key functionality of the Provena source code. All unit tests operate within a mocked environment. Each API's unit tests are located in a dedicated `tests` directory within the component's source code. See each components readme for more info on how to run the unit tests.

### Integration Tests

The Provena repo contains a dedicated integration testing directory, separate from the unit tests defined for each component individually. Unit tests were designed for testing lower level functionality of the Provena source code, meanwhile, the Integration tests were purposed for testing typical user stories. That is, integration tests are high level tests requiring minimal dependency on our source code, but rather, interface with several exposed APIs to test a particular user story. For more info and to run the tests, see the [integration tests readme](./tests/integration/README.md).

### System Tests

These are some basic end-to-end system tests which test core functionality pathways to detect and prevent feature regression as new features are developed. These tests interact with the User Interfaces. For more info and to run the tests, see the [system tests readme](./tests/system/README.md).

# Configuring Provena

Provena features a detached configuration management approach. This means that configuration should be stored in a separate private repository. Provena provides a set of utilities which interact with this configuration repository, primary the `./config` bash script.

```text
config - Configuration management tool for interacting with a private configuration repository

Usage:
  config NAMESPACE STAGE [OPTIONS]
  config --help | -h
  config --version | -v

Options:
  --target, -t REPO_CLONE_STRING
    The repository clone string

  --repo-dir, -d PATH
    Path to the pre-cloned repository

  --help, -h
    Show this help

  --version, -v
    Show version number

Arguments:
  NAMESPACE
    The namespace to use (e.g., 'rrap')

  STAGE
    The stage to use (e.g., 'dev', 'stage')

Environment Variables:
  DEBUG
    Set to 'true' for verbose output
```

The central idea of this configuration approach is that each namespace/stage combination contains a set of files, which are gitignored by default in Provena, which are 'merged' into the user's clone of the Provena repository, allowing temporary access to private information without exposing it in git.

### Config path caching

The script builds in functionality to cache the repo which makes available a given namespace/stage combination. These are stored in `env.json` and has a structure like so:

```json
{
  "namespace": {
    "stage1": "git@github.com:org/repo.git",
    "stage2": "git@github.com:org/repo.git",
    "stage3": "git@github.com:org/repo.git"
  }
}
```

This saves using the `--target` option on every `./config` invocation. You can share this file between team members, but we do not recommend committing it to your repository.

## Config definitions

**Namespace**: This is a grouping that we provide to allow you to separate standalone sets of configurations into distinct groups. For example, you may manage multiple organisation's configurations in one repo. You can just use a single namespace if suitable.

**Stage**: A stage is a set of configurations within a namespace. This represents a 'deployment' of Provena.

## Config repository

The config repository is structured carefully, a copy of the README of the [sample config repository](https://github.com/provena/provena-config-repo-template) is included below

### Purpose

This repository contains configuration files for the Provena project. It serves as a centralized location for managing configuration across different environments and components of the Provena system. This configuration is a mix of sensitive and non-sensitive information, but it is managed centrally to simplify this process.

**Warning: while this repo is private, please don't commit secrets to it, instead commit references/IDs for those secrets stored in AWS Secret Manager**

### `cdk.context.json`

This repo does not contain sample `cdk.context.json` files, but we recommend including this in this repo to make sure deployments are deterministic. This will be generated upon first CDK deploy.

### Structure

The repository is organized using a hierarchical structure based on namespaces and stages:

```
.
├── README.md
└── <your-namespace>
    ├── base
    ├── dev
    └── feat
```

#### Namespaces

A namespace represents a set of related deployment stages, usually one namespace per organisation/use case.

#### Stages

Within each namespace, there are multiple stages representing different environments/deployment specifications

- `base`: Contains common base configurations shared across all stages within the namespace
- `dev`: Sample development environment configurations
- `feat`: Sample feature branch workflow environment configurations

#### Feat stage

The feat stage supports the feature branch deployment workflow which is now a part of the open-source workflow. This makes use of environment variable substitution which is described later.

### File Organization

Configuration files are placed within the appropriate namespace and stage directories. Currently:

```
.
├── README.md
└── your-namespace
    ├── base
    │   ├── admin-tooling
    │   │   └── environments.json
    │   └── utilities
    │       └── supporting-stacks
    │           ├── feature-branch-manager
    │           │   └── configs
    │           │       └── dev.json
    │           └── github-creds
    │               └── configs
    │                   ├── build.json
    │                   └── ops.json
    ├── dev
    │   └── infrastructure
    │       └── configs
    │           └── dev.json
    └── feat
        └── infrastructure
            └── configs
                ├── feat-ui.json
                └── feat.json
```

### Usage by Provena config scripts

#### Base Configurations

Files in the `base` directory of a namespace are applied first, regardless of the target stage. This allows you to define common configurations that are shared across all stages within a namespace.

#### Stage-Specific Configurations

Files in stage-specific directories (e.g., `dev`, `test`, `prod`) are applied after the base configurations. They can override or extend the base configurations as needed.

### Interaction with Provena Repository

The main Provena repository contains a configuration management script that interacts with this configuration repository. Here's how it works:

1. The script clones or uses a pre-cloned version of this configuration repository.
2. It then copies the relevant configuration files based on the specified namespace and stage.
3. The process follows these steps:
   a. Copy all files from the `<namespace>/base/` directory (if it exists).
   b. Copy all files from the `<namespace>/<stage>/` directory, potentially overwriting files from the base configuration.
4. The copied configuration files are then used by the Provena system for the specified namespace and stage.

### Best Practices

1. Use version control: Commit and push changes to this repository regularly.
2. Document changes: Use clear, descriptive commit messages and update this README if you make structural changes.
3. Minimize secrets: Avoid storing sensitive information like passwords or API keys directly in these files. Instead, use secure secret management solutions.

### Config variable substitution syntax

This project supports a syntax for environment variable substitution within JSON files. This feature allows you to create dynamic JSON configurations that can adapt to different environments without modifying the JSON itself.

#### Basic Syntax

The basic syntax for environment variable substitution is:

```
${VARIABLE_NAME}
```

When the JSON is processed, this will be replaced with the value of the environment variable `VARIABLE_NAME`.

### Advanced Syntax

#### Default Values

You can specify a default value to use if the environment variable is not set:

```
${VARIABLE_NAME:-default_value}
```

#### Conditional Substitution

For more complex scenarios, you can use conditional substitution:

```
${VARIABLE_NAME?value_if_set||value_if_not_set}
```

### Examples

Here are some examples to illustrate the different substitution patterns:

1. Basic substitution:

   ```json
   {
     "database_url": "${DB_URL}",
     "port": ${PORT:-8080}
   }
   ```

2. Conditional substitution:

   ```json
   {
     "debug_mode": "${DEBUG?'true'||'false'}",
     "log_level": "${LOG_LEVEL?'debug'||'info'}"
   }
   ```

3. In-line substitution:

   ```json
   {
     "api_endpoint": "https://${API_HOST:-api.example.com}:${API_PORT:-443}/v1"
   }
   ```

4. Complex conditional substitution:
   ```json
   {
     "database": {
       "host": "${DB_HOST}",
       "port": "${DB_PORT?!!||5432}",
       "ssl": "${DB_SSL?true||false}",
       "ssl_cert": "${DB_SSL?'${SSL_CERT_PATH}'||null}"
     }
   }
   ```

### Special Case: Self-Referential Substitution with quotation stripping

A particularly useful pattern is the self-referential substitution with quotation stripping.

```json
{
  "git_commit_id": "${GIT_COMMIT_ID?'!!'||null}"
}
```

The goal of the above syntax is to

- allow you to have control over whether the output is quoted or not
- ensure the original JSON remains valid/parseable before substitution
- allow you to reference the variable value as part of conditional logic

There is a special condition in the config script as follows

**If a conditional substitution is directly surrounded by double quotes, then remove those double quotes from the output**

There are also two general rules:

- always replace `'` with `"`
- always replace `!!` with the value of the variable

Combining these two features means

```json
{
  "git_commit_id": "${GIT_COMMIT_ID?'!!'||null}"
}
```

can resolve to two values

- if `GIT_COMMIT_ID` is not "falsey" (i.e. not defined or literal value 'false') then the output will be

```
{
  "git_commit_id": "123456"
}
```

- if `GIT_COMMIT_ID` is not defined then

```
{
  "git_commit_id": null
}
```

## Using the config script

Given the above information, a common use would be to 'checkout' configuration files for a target deployment to operate the system, e.g.

```bash
./config namespace stage
```

# Documentation

### General Provena Docs

[Click here for general purpose Provena documentation](http://docs.provena.io/)

### API endpoint documentation

Individual API documentation can be found at _endpoint_/docs or _endpoint_/redoc. This is useful for inspecting the payloads and available endpoints of each API.

## License

Provena is available via an open-source licence (BSD 3-clause) allowing your project to deploy an instance with freedom to operate.

## Contact Information

Contact Provena Developers via [https://www.csiro.au/en/contact](https://www.csiro.au/en/contact)

## Contributing

### TODO

## Acknowledgements

The development of Provena Version 1.0 was funded by Reef Restoration and Adaptation Program (RRAP), which is a partnership between the Australian Government’s Reef Trust and the Great Barrier Reef Foundation. Provena has been developed to support the Modelling and Decision Support (MDS) Subprogram (https://gbrrestoration.org/program/modelling-and-decision-support/).

People who contributed and developed Provena (ordered alphabetically):

- Andrew Freebairn
- David Lemon
- Fareed Mirza
- Jevy Wang
- Jonathan Yu
- Linda Thomas
- Omid Rezvani
- Peter Baker
- Ross Petridis
- Sharon Tickell
- Simon Cox
- Xinyu Hou
