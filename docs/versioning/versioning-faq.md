---
layout: default
nav_order: 3
title: Versioning FAQ 
has_children: false
parent: Versioning
---
# Versioning Frequently-asked-questions 

## What's the difference between a version and metadata history?

Metadata history is a lightweight change tracking (typos, metadata corrections). Reasons for updating metadata:
- Adding a citation
- Minor updates to the description or the title of the item (e.g. dataset, model)

Versioning an item creates a new entity in Provena. This entails minting of a new identifier and new entity that is linked to the previous version of the item. It gives users the ability to signal that there is a new version of a thing. Reasons for a new version could be: 
- The process that led to the creation of the item has changed (e.g. produced by a different model algorithm)
- The previous version has fundamental errors in its content (e.g. data files, code) and requires correction.

## Are users able to create a version from a previous version, rather than the latest?

No - Provena doesn't allow creating a version from a previous version, i.e.  version branching. This would raise issues such as merging, dangling branches, etc. These are currently out of scope.

Provena implements a simple versioning scheme where versions is created from the latest version. 

##  What's the difference between the 'clone' feature and the 'versioning' feature?

Functionality wise, the clone and versioning feature looks similar - metadata is copied, and a new identifier is minted for the item. The difference is that for a new version:
- the new versioned item is linked to the previous version of the item
- a version activity is generated in the provenance graph linking the versioned items with each other

## What happens when a version is created for Datasets?

When a new version is created for a Dataset and if users want to use the Provena data storage feature, a new storage location is created. This storage location will be empty for users to upload relevant data for that version.

