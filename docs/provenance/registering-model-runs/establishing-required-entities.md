---
layout: default
title: Establishing required entities
nav_order: 1
has_children: false
grand_parent: Provenance
parent: Registering model runs
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

# Establishing required entities

As part of creating high quality provenance, key identities must be registered before being referenced by their [persistent identifiers](../../digital-object-identifiers.md) in model run records.

For more information about the provenance conceptual model, see [what is provenance](../overview/what-is-provenance.html).

## When to create and when to reuse

The [registry](../registry/index.html) contains various types of things.

Some entries refer to persistent things (continuants) which can participate in multiple activities or events, such as:

-   agents
    -   people
    -   organisations
-   entities
    -   models
    -   dataset templates
    -   workflow templates

Some entries relate to things that happened (occurrents) which will not be later re-used:

-   activities
    -   model runs

Whenever we refer to reusable things, it is critical to the integrity of the provenance graph that a consistent identifier is used, so that we know we are talking about the same thing.

For example - before registering a new organisation, ensure that the organisation doesn't already exist.

To discover existing entities, you can [explore the registry](../registry/exploring_the_registry.html).

## What entities are required to register provenance?

Before creating a [model run workflow template](./model-workflow-configuration.html), some entities must be registered.

These entities describe:

-   who registered the model run?
-   what model is the model run using?
-   what organisation is associated with the model run?

All model runs must be linked to these contextualising entities.

Before registering a reusable entity, such as those below, ensure the [entity doesn't already exist](#when-to-create-and-when-to-reuse). You can find records by [exploring the registry](../registry/exploring_the_registry.html).

The below sections will provide specific advice on how to create each entity type. If you aren't sure how to use the entity registry and would like more specific guidance on how to login, request access, register, update and find entities, read more [here](../registry/index.html).

{% include warning.html content="From this point on, it is assumed that you know how to use the entity registry to create, update, find and share entities. If not, you should see our documentation <a href=\"../registry/index.html\">here</a> before proceeding." %}

### Person

#### What is a Person Entity?

A person is a type of Agent in the [provenance conceptual model](../index.html). All modelling activity must be attributed to an agent that performed it. Currently, this agent is assumed to be a Person, though other types of agents may be registrable in the future.

#### How to register a Person Entity?

Start by [exploring the registry](../registry/exploring_the_registry.html) to ensure that a record describing you (or the agent you are registering) does not already exist in the registry.

Navigate to the new entity form (for help, see [registering an entity](../registry/registering_and_updating.html)). Select the "Person" entity type. Information on the various metadata fields has been provided below.

-   **Display Name**\*: How would you like your name to appear when viewed as a system entity? E.g. "Peter Baker"
-   **Email**\*: Your email address, please specify the email address that you have logged in with if registering yourself e.g. "your.email@gmail.com"
-   **First Name**\*: Your first name, e.g. Peter
-   **Last Name**\*: Your last name, e.g. Baker
-   **Open Researcher and Contributor ID ([ORCID](https://orcid.org){:target="\_blank"})** : An ORCID uniquely identifies you as an academic Person. Providing an ORCID is optional though recommended if you are registered. To select an orcid, you can search for your name and organisation using the tool e.g. "Peter Baker CSIRO". When you see your name appear, click it in the list and the form will show your selection. Alternatively, you can directly copy your ORCID iD in the form XXXX-XXXX-XXXX-XXXX into the box and select the matching result.
-   **Ethics Approved**\*: Have you received consent and been granted permission from the person to be registered in the registry? If you do not approve, the Person cannot be registered. By registering a person, you consent to:
    1.  Having a Handle identifier being assigned to the person
    1.  The person being included and referenced in provenance and dataset records in the information system
    1.  Enabling users of the information system to query the system using the person identifier, e.g. related provenance and/or data records

{% include warning.html content="All Person(s) registered in the Entity Registry must supply explicit consent for their registration and usage in the system. For this reason, we recommend that you only register yourself as a Person in the RRAP IS Registry. If someone requests that you register them in the system, you should recommend that they instead login and perform the process themselves. If it is required that you register someone else's identity, please ensure you explicitly seek their consent." %}

Once you have completed your registration, you can view the record and take note of the identifier (noting that you can find your entity again at any time by [exploring the registry](../registry/exploring_the_registry.html)).

### Organisation

#### What is an Organisation Entity?

An organisation is a type of Agent in the [provenance conceptual model](../index.html). All modelling activity is associated with a registered organisation.

#### How to register an Organisation Entity?

Start by [exploring the registry](../registry/exploring_the_registry.html) to ensure that a record describing the organisation does not already exist in the registry.

Navigate to the new entity form (for help, see [registering an entity](../registry/registering_and_updating.html)). Select the "Organisation" entity type. Information on the various metadata fields has been provided below.

-   **Display Name**\*: How would you like the name of the organisation to appear when viewed as a system entity? E.g. "CSIRO"
-   **Name**\*: What is the full title/name of the organisation e.g. "Commonwealth Scientific and Industrial Research Organisation"
-   **Research Organisation Registry Identifier ([ROR](https://ror.org){:target="\_blank"})** : A ROR ID uniquely identifies a research organisation. It is likely that the organisation you are registering has an ROR. It is optional to provide the ROR, though recommended. To select a ROR, you can search for the name of the organisation e.g. "CSIRO". When you see the desired organisation appear, click it in the list and the form will show your selection.

Once you have completed your registration, you can view the record and take note of the identifier (noting that you can find your entity again at any time by [exploring the registry](../registry/exploring_the_registry.html)).

### Model

#### What is a Model Entity?

A model is a type of Entity in the [provenance conceptual model](../index.html). The model entity references the software/model that was run in a modelling activity. The model entity persists beyond a particular software version. The software version is identified as part of the [model run workflow template](./model-workflow-configuration.html).

#### How to register a Model Entity?

Start by [exploring the registry](../registry/exploring_the_registry.html) to ensure that a record describing the model does not already exist in the registry.

Navigate to the new entity form (for help, see [registering an entity](../registry/registering_and_updating.html)). Select the "Model" entity type. Information on the various metadata fields has been provided below.

-   **Display Name**\*: How would you like the model's name to appear when viewed as a system entity? E.g. "MALM"
-   **Name**\*: The complete title of the model e.g. "Marine and Land Model"
-   **Description**\*: A description of the model which assists other users in understanding the nature of the model.
-   **Documentation URL**\*: A URL to a website which contains information or documentation about the model.
-   **Source URL**\*: A URL to a website which contains the source code/contents of the model.

Once you have completed your registration, you can view the record and take note of the identifier (noting that you can find your entity again at any time by [exploring the registry](../registry/exploring_the_registry.html)).
