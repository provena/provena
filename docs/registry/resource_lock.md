---
layout: default
title: Resource Locks
nav_order: 6
parent: Registry
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

## What is a resource lock?

Resources in the Registry can be "locked" to prevent changes to the resources's metadata (and dataset files, if applicable) until it is unlocked.

## What happens when a resource is locked?

### Registry Entities

Locked resources cannot be edited. When viewing a registry entity, the "Edit Entity" button will not appear and the API will block this operation.

### Datasets

Locked datasets are displayed differently to Data Store users. A locked dataset is indicated by a grey lock icon in the settings and upload tabs.

The locking of a dataset is not just cosmetic, the APIs which grant credentials will enforce this status, responding with an error message in the case of an invalid request, as shown below.

|                             Requesting upload credentials for a locked dataset                             |
| :--------------------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/dataset_lock/locked_api_error.png" alt="drawing" width="600"/> |

If a dataset is locked, the upload tab will show a customised message:

|                                  View of locked Dataset in upload tab                                   |
| :-----------------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/dataset_lock/upload_locked.PNG" alt="drawing" width="600"/> |

## Who can lock a resource?

Resource locks can be applied and removed by users who have administrative access to the resource. See [access control](./access-control.html){:target="\_blank"} for more information about resource access.

## How to add or remove a resource lock

To apply or remove a lock, navigate to the resource in the Registry, select the "settings" tab (1), then the "Lock Settings" drop down (2), and finally, "Lock The Resource" (3).

|                                        Accessing lock controls                                         |
| :----------------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/dataset_lock/finding_lock.png" alt="drawing" width="600"/> |

A helpful, brief justification must be provided for the lock or unlock action. Your identity (email) and justification will be logged in the resources's lock history (visible below). As an example of a suitable lock justification is "completed initial round of modelling and outputs finalised".

|                                            Resource lock history                                             |
| :----------------------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/dataset_lock/lock_event_history.PNG" alt="drawing" width="600"/> |
