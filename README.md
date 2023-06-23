# Provena

Provena is an information system built to capture, manage, and analyse [Provenance](https://ardc.edu.au/resource/data-provenance) records, and their artefacts. Provena additionally implements a robust data storage solution for seamless interaction with and inspection of the data referenced in provenance records.

## Description

To facilitate system functionality, Provena implements a suite of components. Each comprise of a Docker deployed Python FastAPI serverless microservice, and where user interaction is required, these APIs are paired with a front-end web application. The following components are implemented:

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

-   individual record registration (using the Pydantic models directly)
-   CSV bulk model run record ingestion (using a job queue workflow deployed separately)

Workflow provenance can support transparency of the modelling activities and facilitate repetition of the knowledge generation activity. Provenance can also assist in determining the integrity of certain knowledge and knowledge generation activities where important decisions are based off of this knowledge.

The Provena Provenance Store UI is a Typescript React GUI which enables user friendly interaction with the Provena Provenance API and Registry API.

This UI facilitates

-   interactive visualisation of provenance graphs
-   tooling to assist with bulk registration of provenance model run activities

and more...

For more info on the Provena Provenance API and UI:  
[Provenance API Readme](./prov-api/README.md)  
[Provenance UI Readme](./prov-ui/README.md)

**Authorisation Service (API)**

The Provena Auth API provides a set of user and admin tools which assists with:

-   creating, viewing and managing system access requests
-   generating access reports which assess the current users access to the components configured in the system Authorisation Model
-   creating, querying and managing user groups
-   managing the User to Registry Person Link

The Auth API is used heavily by other APIs as it communicates with the User groups table to enable querying of group membership. This group information is used to enforce resource level permissions on registry items.

For more info on the Authentication API:  
[Authentication API Readme](./auth-api/README.md)

**Search Service (API)**

This API exposes a registry search endpoint which queries an Elastic Search index of the Registry.

The Search API is used across many of the Provena UIs as a simple way to search for registered items.

For more info on the Search API:  
[Search API Readme](./search-api/README.md)

## System Architecture

The following diagrams represent that basic architecture of the system:

### TODO

## Technologies Used

Give a brief description, purpose, and justification of choice for each technology used in Provena.

### TODO

-   Fast API, typescript, dynamo, neo4j, github, aws (pipelines, ec2 instances?), authentication
    what else?

## Getting Started

### Deploying and managing Provena

**We recommend that new users, who want to deploy Provena, visit our thorough deployment guide available here: [Provena from Scratch](https://confluence.csiro.au/display/RRAPIS/HOW+TO+Deploy+Provena+from+SCRATCH).**

### Deploying APIs and UIs

Once a Provena deployment has been configured and deployed as per the above guide, individual APIs and UIs can be deployed for development, debugging or testing purposes by following instructions in their respective READMEs.

## Usage

Provena comes with a suite of fully developed User Interface web pages that facilitate a user friendly interaction with the Provena APIs and resources.

Additionally, Provena has well documented REST APIs (see API endpoint documentation) which can be interacted with directly using a REST client such as Postman or thunderclient, or programmatically using Python, for example. Programmatic interactions are recommended for our power users and we have guide on authentication for this.

### TODO

_LINK TO DOCUMENTATION ON PROGRAMATIC INTERACTIONS WITH PROVENA_

## Testing

## Component Unit tests

Each API component has a dedicated unit test suite. Unlike the Integration tests which are purposed for testing user stories and interacts between multiple APIs at once, the unit test were designed to test individual endpoints and key functionality of the Provena source code. All unit tests operate within a mocked environment. Each API's unit tests are located in a dedicated `tests` directory within the component's source code. See each components readme for more info on how to run the unit tests.

### Integration Tests

The Provena repo contains a dedicated integration testing directory, separate from the unit tests defined for each component individually. Unit tests were designed for testing lower level functionality of the Provena source code, meanwhile, the Integration tests were purposed for testing typical user stories. That is, integration tests are high level tests requiring minimal dependency on our source code, but rather, interface with several exposed APIs to test a particular user story. For more info and to run the tests, see the [integration tests readme](./tests/integration/README.md).

### System Tests

These are some basic end-to-end system tests which test core functionality pathways to detect and prevent feature regression as new features are developed. These tests interact with the User Interfaces. For more info and to run the tests, see the [system tests readme](./tests/system/README.md).

## Documentation

### TODO

Where is the general purpose documentation hub for Provena?

### API endpoint documentation

Individual API documentation can be found at _endpoint_/docs or _endpoint_/redoc. This is useful for inspecting the payloads and available endpoints of each API.

## License

Provena is available via an open-source licence (BSD 3-clause) allowing your project to deploy an instance with freedom to operate.

## Contact Information

### TODO

Determine desired email address for contact.

To contact the Provena development team, use this email address: [@csiro.au](mailto:@csiro.au)

## Contributing

### TODO

## Acknowledgements

### TODO
