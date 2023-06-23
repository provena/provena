---
layout: default
title: Model run overview
nav_order: 1
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

# Model run overview

## What is a model run?

Model runs are an activity (as per the [PROV Ontology](https://www.w3.org/TR/prov-o/)) which form a critical piece of our [provenance conceptual model](../../overview/what-is-provenance). Once registered, a model run will have a persistent identifier and be discoverable in the [Registry](../../registry/overview) and explorable in the [Provenance Store](../../exploring-provenance/index).

It is useful to think of the modelling process as a discrete series of "model runs" - where a model run accepts some inputs, and produces some outputs.

Considering modelling as a series of activities enables us to understand, record and explore the lineage of an entity. It is possible, and likely, that modelling activities will consume (as inputs) the outputs of other modelling activities.

## Prerequisites

Before registering a model run record, you need to have registered or identified a [Person](../establishing-required-entities#person), an [Organisation](../establishing-required-entities#organisation) and a [Model](../establishing-required-entities#model). See [establishing required entities](../establishing-required-entities) for more information.

A model run record references a [Model Run Workflow Template](../model-workflow-configuration#model-run-workflow-template) which uses [Dataset Templates](../model-workflow-configuration#dataset-template). For more information about configuring your workflow, see [workflow configuration](../model-workflow-configuration).

You will also need to use the [Data Store](../../../data-store/overview) to register and populate the input and output datasets referenced in your model run. More information about datasets and provenance is included below in [provenance and datasets](#provenance-and-datasets).

## Payload information

A model run _uses_ a [Model](../establishing-required-entities#model) and _is associated with_ a [Person](../establishing-required-entities#person) and an [Organisation](../establishing-required-entities#organisation).

A model run satisfies or realises a [model run workflow template](../model-workflow-configuration#model-run-workflow-template). For each input and output [dataset template](../model-workflow-configuration#dataset-template) referenced in the workflow template, a dataset must be provided. If [deferred resources](../model-workflow-configuration#dataset-template) were used, then the path to these resources in the dataset must be specified.

The section below will provide a detailed breakdown of a model run record.

### Model run record fields

The schema which is validated by the provenance API is available [here](https://prov-api.mds.gbrrestoration.org/docs#/Model%20Runs/register_complete_model_run). A summary is provided below:

-   **workflow_template_id**\*: The entity registry identifier of the model run workflow template which this model run is using. See [Model Run Workflow Template](../model-workflow-configuration#model-run-workflow-template) for more information.
-   **description**\*: A description of the model run. The text in this field is searchable, and should help yourself and others understand the purpose, inputs and outputs of this model run.
-   **associations**\*:
    -   **modeller_id**\*: The entity registry identifier of the [Person](../establishing-required-entities#person) who is registering the model run record
    -   **requesting_organisation_id**\*: The entity registry identifier of the [Organisation](../establishing-required-entities#organisation) responsible for the model run activity.
-   **start_time**\*: The starting execution time of the model run in [unix epoch timestamp](https://en.wikipedia.org/wiki/Unix_time) format
-   **end_time**\*: The ending execution time of the model run in [unix epoch timestamp](https://en.wikipedia.org/wiki/Unix_time) format
-   **annotations**: A map of key value pairs which correspond to either required or optional workflow annotations specified in the model run workflow template. If mandatory annotations specified in the workflow template are not provided here, the model run will be invalid. e.g. `{"key1" : "value", "key2" : "value2}`.
-   **inputs**\*: A model run must specify a dataset and the path of any deferred resources for each of the model run workflow template inputs. Inputs are objects of the following format:
    -   **dataset_template_id**\*: The entity registry identifier of the [Dataset Template](../model-workflow-configuration#dataset-template) listed as an input in the workflow template.
    -   **dataset_id**\*: The data store identifier of the dataset satisfying this template used in the model run
    -   **dataset_type**\*: The type of dataset - currently this has to be set to the only option "DATA_STORE"
    -   **resources**: A map of key value pairs which specify a file path in the dataset for each of the deferred resources in the dataset template, if any. E.g. `{"configuration_file" : "config/inputs/configuration_file.csv", "geometry_file":"geometries/corals.json"}`.
-   **outputs**\*: A model run must specify a dataset and the path of any deferred resources for each of the model run workflow template outputs. Outputs are specified using the same fields as inputs (above).

## Provenance and datasets

A model run uses zero or more datasets as input, and produces zero or more datasets as output. The provenance system verifies that the dataset identifiers specified are valid, and exist in the data store, however, it does not investigate the contents of the input or output datasets. It is the responsibility of the user to populate the registered dataset(s) with the appropriate files specified in the dataset template(s).

For more information about datasets, visit the [Data Store documentation](../../../data-store/overview).

## What next?

Understanding the model run record is critical to the next step - registering model run records.

There are two primary methods of registering provenance in a scalable way.

If you would like to work directly with the [Provenance Store API](https://prov-api.mds.gbrrestoration.org/docs) you can follow [this guide](./register-model-run-records-by-api).

If you would prefer to record and lodge model runs in a special system generated CSV template, you can follow [this guide](./register-model-run-records-by-csv-template).
