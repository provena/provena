---
layout: default
title: Describing a dataset
nav_order: 4
grand_parent: Provena
parent: Data store
---

{: .no_toc }

# Describing a dataset (metadata)

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

The Data Store will have a minimal dataset metadata record schema using [RO-CRATE](https://w3id.org/ro/crate){:target="\_blank"} as the metadata data file format. The minimal dataset metadata record fields are:

## User entered data fields

{% include_relative user-metadata-fields.md %}

## Generated data fields

{% include_relative generated-metadata-fields.md %}

The metadata fields included in Data Store enables data registration, upload, sharing via the S3 APIs (application programming interface) to support current modelling activities in M&DS. Future releases will incrementally add additional capability to capture RRAP M&DS, ISO and Science related metadata for when we need wider data publication.

---
