---
layout: default
title: Cloning an Item
nav_order: 8
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

# Cloning an Item

## What does it mean to clone an item?

In the registry, you can _clone_ an item. Cloning an item is the same as registering a **new** item, however the form is prefilled with the details of an existing record.

**Cloning a dataset does not copy any dataset files**. For more information, see the [FAQ](#faq).

This enables you to quickly produce multiple records with similar contents.

This could be useful for producing similar [Datasets](../../data-store/overview) or [Dataset Templates](../provenance/registering-model-runs/model-workflow-configuration#dataset-template), for example.

## How to clone an item in the Registry

### Required Permissions

To clone an item you need to be able to read the metadata of the item being cloned, and write to the Registry. In particular you need the following permissions:

-   Registry Write (general user permission)
-   Metadata Read (item specific permission)

### Process

Start by [exploring the registry](./exploring_the_registry) to find the item you want, then [view it's details](./exploring_the_registry#viewing-records).

If you have the appropriate permissions, as mentioned [above](#required-permissions), you will see the 'Clone Entity' button appear in the top panel (1).

|                                     Clone Entity Button                                      |
| :------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/clone_item_button.png" alt="drawing" width="800"/> |

Clicking the clone button will bring you to the registration form. From there, you can edit the pre-filled details and create the new item.

|                                     Clone Entity Form                                      |
| :----------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/clone_item_form.png" alt="drawing" width="800"/> |

## FAQ

**Can I clone a Dataset?**

Datasets can be cloned, however the clone **does not include any dataset files**, only the metadata. To clone a dataset, click "View in Datastore" in the top buttons panel. The "Clone Dataset" button will appear in the same location as the Registry, if you have the required permissions.

**Are the access settings cloned from the source item?**

No, cloning an item is equivalent to creating a new item with existing details pre-filled. Any access settings applied to the source item will not be transferred to the destination item.

**Is the history of the source item copied?**

No, cloning an item is equivalent to creating a new item with existing details pre-filled. The history of the source item is not part of the history of the new item.

**Does the Provena API support cloning?**

No, cloning is not implemented for programmatic API use. Instead, you can `fetch` the contents of an existing record, modify them, and post the new item using the appropriate `create` endpoint.
