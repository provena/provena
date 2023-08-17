---
layout: default
nav_order: 2
title: Versioning Overview
has_children: false
parent: Versioning
---

# Versioning Overview

Provena provides the capability to version certain types of Entities in the Registry, including datasets. The purpose of this feature is to allow users to create and manage versions of registered items. Users can version items to mark items at a point in their development or release lifecycle. Users can then manage and refer to distinct versions of an item, each with a unique [persistent identifier](../digital-object-identifiers).

By tracking different versions of registered items, users can produce more accurate provenance trails. For example, version 1 of _Dataset X_ uses a different configuration of a modelling software suite to version 2 of _Dataset X_.

Other use cases include:

-   Marking a previous version of an item as deprecated or erroneous
-   Maintaining two versions of items that are both valid, but have different lineages

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

1. A new [persistent identifier](../digital-object-identifiers) is minted for each version (i.e. a new Handle ID)
2. A versioned item is timestamped
3. A new activity is created in the Registry. This activity is of type _Version_. If you explore the [Provenance Graph](../provenance/exploring-provenance/Explore%20Graph) you will see that the _Version_ activity links the previous item, to the new item, and associates it with the _Agent_ that created the version.
4. The new item is assigned a version number, determined by incrementing the previous item's version number by 1
5. Versioned items shall link to the previous revision. Users should be able to navigate back to other versions (previous and later versions)
6. A versioned item is a separate entity to other versioned items. Users should be able to view a versioned item independently of previous versions
7. Provena provides functionality to navigate to the current revision and previous revisions distinctly

## Next steps

-   [Versioning FAQs](./versioning-faq.html)
-   [How to create versions in the Registry](./how-to-version.html)
-   [How to create versions in the Data Store](./how-to-version-in-data-store.html)
-   [How to view version information and lineage](./how-to-view-versions.html)
