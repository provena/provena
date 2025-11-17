---
layout: default
nav_order: 2
title: Versioning Overview
has_children: false
parent: Versioning
---

Artefacts evolve over time—whether through improved inputs, error corrections, or updated model parameters/configurations. 
To ensure reproducibility and traceability, it is essential to identify the source and history of each version, along with its attribution.
Provena provides capability for versioning a subset of entity types in the Registry, including datasets. 

The purpose of this feature is to allow users to create and manage versions of registered items in Provena. Each version is a distinct entity in the Provena Registry, so users can manage and refer to versions of an item as first class items. This allows users to accurately refer to components used in a provenance trail, e.g. version 1 of Dataset X uses a different configuration of a modelling software suite to version 2 of Dataset X.

Use cases include:
* Versioning items to mark items at a point in their development or release lifecycle
* Creating a version of the item as the item is now deprecated or erroneous
* Maintaining two versions of items that are valid but have different lineages and uses

The screenshot below shows an example set of versions created for a dataset.

|                 Example dataset version info                  |
| :---------------------------------------------------------------------------------------: |
| <img src="../assets/images/versioning/versioning-overview-1.png" alt="drawing" width="600"/> |


## Principles

Users can register and reference specific versions of entities in Provena, each assigned a persistent identifier, at a point in the development. This enables users to track changes over time and ensures that operational decisions can be linked to the exact versions used. 

Key principles of versioning in Provena:
1.	Versioning marks a change in an entity’s lifecycle, such as updates or deprecations
2.	Multiple versions of items may be maintained as valid entities 
3.	Only endurant items (objects that persist) that are a subset of the Entity type are versioned: Dataset, Model, Dataset Template, Model Run Workflow Template. Instances of Agents and Activities cannot be versioned as they have a temporal element, i.e. Person, Organisation, and Model Run. 
4.	Each versioned item is a distinct entity, allowing precise referencing in provenance trails. 

As Provena’s underlying semantics are grounded using the PROV ontology, we  implement versioning as an extension of the PROV by extending the prov:Activity class with a “Version” class. Figure 6 shows the Version class extension of prov:Activity in context. Since instances of “Version” is a prov:Activity, we inherit the following relationships: prov:wasGeneratedBy, prov:used, and prov:wasAssociatedWith. A version activity instance is registered as a record in the Provena system linking the previous item (via prov:wasGeneratedBy relation) to the new item (via prov:used relation) and associating it with the Agent that created the version (via prov:wasAssociatedWith relation). 


## What can be versioned?

All registered items which are in the _Entity_ category, can be versioned. For more information about the categories of registered items, see the [provenance overview](../provenance/overview/what-are-entities).

This includes:

-   Dataset
-   Model
-   Dataset Template
-   Model Run Workflow Template

## What cannot be versioned?

_Agents_ and _Activities_ cannot be versioned, this includes:

-   Person
-   Organisation
-   Model Run

## What happens when an item is versioned

1. A new [persistent identifier](../digital-object-identifiers) is minted for each version (i.e. a new Handle ID). This is maintained in the Registry and uniquely identifies each version as a first-class entry in the Registry. Versioned entities can then be referenced individually in provenance chains.
2. A versioned item is timestamped
3. A new activity is created in the Registry. This activity is of type _Version_. If you explore the [Provenance Graph](../provenance/exploring-provenance/Explore%20Graph) you will see that the _Version_ activity links the previous item, to the new item, and associates it with the _Agent_ that created the version.
4. The new item is assigned a version number, determined by incrementing the previous item's version number by 1
5. Versioned items shall link to the previous revision. Users should be able to navigate back to other versions (previous and later versions)
6. A versioned item is a separate entity to other versioned items. Users should be able to view a versioned item independently of previous versions
7. Provena provides functionality to navigate to the current version and previous versions distinctly
8. When a new version is created for a Dataset and if users want to use the Provena data storage feature, a new storage location is created. This storage location will be empty for users to upload relevant data for that version. While this approach maximises flexibility, it does not compute file-level differences which may lead to duplication and less efficient dataset storage. 


## Next steps

-   [Versioning FAQs](../faq.html#versioning)
-   [How to create versions in the Registry](./how-to-version.html)
-   [How to create versions in the Data Store](./how-to-version-in-data-store.html)
-   [How to view version information and lineage](./how-to-view-versions.html)
