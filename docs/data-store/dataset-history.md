---
layout: default
title: Dataset metadata history
nav_order: 14
grand_parent: Information System
parent: Data store
---

{: .no_toc }

# Dataset metadata history

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## What is Dataset metadata history?

Datasets are registered records in the [Registry](../provenance/registry/overview). This means that changes to the **metadata** of a dataset are recorded. Each change produces a new iteration or version of the dataset metadata.

## Does this include the files within a dataset?

Currently, the history of a dataset refers **only** to the metadata of the dataset (information about the dataset and it's files). This means that reverting to a previous version **does not restore the files at that point in time**.

If you need to revert your dataset's files to a previous point in time, please contact us.

## How do I explore and revert to previous versions?

The data store's dataset detail view (see [viewing a dataset](./viewing-a-dataset)) includes a history tool - this tool operates identically to the registry's history feature. The tool will appear if a dataset has multiple history entries. The history tool is highlighted below:

|                                      Dataset History                                      |
| :---------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/dataset_history.png" alt="drawing" width="800"/> |

For instructions on how to use this tool, see [registry item history](../provenance/registry/item_history).
