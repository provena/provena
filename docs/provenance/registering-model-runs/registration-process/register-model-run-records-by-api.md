---
layout: default
title: Register model run records by API
nav_order: 2
has_children: false
grand_parent: Registering model runs
parent: Creating and registering model run records
---

{: .no_toc }

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

# Register model run records by API

Directly registering model run records by using the Provenance Store [API](https://en.wikipedia.org/wiki/API) is an efficient and scalable approach.

Provena APIs can be integrated in an automated way into any internet connected computing environment.

See the sections below for information about how to use the API.

## Endpoints and documentation

The Provena APIs are [REST](https://www.redhat.com/en/topics/api/what-is-a-rest-api)ful Python [ASGI](https://asgi.readthedocs.io/en/latest/) compliant services. All APIs exposes two documentation endpoints. The Provenance API documentation is linked below:

-   Provenance Store API
    -   [Swagger](https://swagger.io) documentation - [https://prov-api.mds.gbrrestoration.org/docs](https://prov-api.mds.gbrrestoration.org/docs)
    -   [Redoc](https://github.com/Redocly/redoc) documentation - [https://prov-api.mds.gbrrestoration.org/redoc](https://prov-api.mds.gbrrestoration.org/redoc)

## Authentication and authorisation

All Provena APIs use the same authorisation workflow.

You can learn about using the Provena APIs [here](../../../API-access/index). You can learn about authorising [here](../../../API-access/authentication/index).

## Example payloads

All Provena APIs use JSON to communicate. This object notation is easy to read for computers and humans.

All endpoints are automatically documented, including structurally valid example payloads, see [documentation](#endpoints-and-documentation) above.

Below, we will provide some examples of structurally valid payloads for provenance API endpoints.

The IDs and values used in these records are not real.

### Model Run Record

```json
{
    "workflow_template_id": "1234",
    "model_version": "1.2",
    "inputs": [
        {
            "dataset_template_id": "1234",
            "dataset_id": "1234",
            "dataset_type": "DATA_STORE",
            "resources": {
                "configuration_file": "data/configuration/config1234.csv"
            }
        }
    ],
    "outputs": [
        {
            "dataset_template_id": "1234",
            "dataset_id": "1234",
            "dataset_type": "DATA_STORE"
        }
    ],
    "annotations": {
        "RCP": "45",
        "species": "speciesA"
    },
    "study_id" : "1234",
    "description": "This model run is not real but is used to demonstrate the model run record payload structure.",
    "associations": {
        "modeller_id": "1234",
        "requesting_organisation_id": "1234"
    },
    "start_time": 1669355820,
    "end_time": 1669442219
}
```
<!---
## Example notebooks

To provide end to end examples of common API driven workflows, we have a blog style series of notebooks available [here](https://gbrrestoration.github.io/rrap-demo-blog/).

The [modelling workflow demonstration notebook](https://gbrrestoration.github.io/rrap-demo-blog/jupyter/2022/09/09/rrap-is-workflow.html) provides an end to end example of managing data and provenance in the RRAP IS.
-->
