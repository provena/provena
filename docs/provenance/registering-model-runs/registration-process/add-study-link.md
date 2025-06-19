---
layout: default
title: Adding a study link to an existing record
nav_order: 4
has_children: false
grand_parent: Provenance
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

# Adding a study link to an existing record

Sometimes, model runs which are part of a [Study](../establishing-required-entities#study) are registered before the Study is ready, or this link is missed during registration. Provena allows you to add a link to a Study on an existing model run, as long as

- the model run is registered and available in the [Registry](../../../registry/overview)
- the model run does not already have a linked Study - this field is described in [model run fields](./overview#model-run-record-fields)
- the study to be linked is registered in the Registry and you [have permission to edit it's metadata](../../../registry/access-control)

## How to link a model run to a study

This process is quick and easy provided that the above pre-requisites are in place.

The process involves

- navigating to your model run in the Registry
- using the 'Link to study' tool

### Find your model run in the Registry

Following the instructions [here](../../exploring-provenance/discovering-records), find your existing model run in the Registry, your page should look like this:

|                                            Model run details page                                             |
| :-----------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/model_run_details.png" alt="drawing" width="800"/> |

### Use the 'Link to study' tool

In the below image, you will see this highlighted button.

|                                               Link button                                               |
| :-----------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/link_button.png" alt="drawing" width="800"/> |

If you cannot see this button, it means that the registered model run is already linked to a Study or you do not have permission to perform this action.

Once you can see the button, click it, and you will see the following popup dialog:

|                                            Popup details                                            |
| :-------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/popup_1.png" alt="drawing" width="800"/> |

This dialog requests that you identify the Study you would like to link to this model run. To do so, you can search (1), or enter the [Handle ID](../../../digital-object-identifiers) of the registered Study (2). After entering the manual ID, you can submit it by pressing enter or (3). If you would like to [explore the Registry](../../../registry/exploring_the_registry) to find your study, you can use the deep link (4) which will take you to a filtered view of only Studies in the Registry.

For example, we search for a study called "Simple study", and select it from the drop down:

|                                          Search for study                                          |
| :------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/simple.png" alt="drawing" width="800"/> |

Then, you will see the following view

|                                          Confirm selection                                          |
| :-------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/confirm.png" alt="drawing" width="800"/> |

The green tick (1) indicates that this selection is valid. If you would like to clear this selection, press (2). If you are ready to submit this link, hit (3). If you would like to cancel the operation, press (4).

{% include warning.html content="Once you link your model run to a Study, there is no way to remove this link. Please double check you would like to add this link before submitting." %}

Submission should be quick, and you will be returned to the details page, where you can see the new link:

|                                               New study link                                               |
| :--------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/provenance/add_study_link/new_study_link.png" alt="drawing" width="800"/> |

If you experience any errors, it's always worth refreshing the page and trying again, otherwise, contact your system administrator.

{% include warning.html content="The provenance graph will not immediately reflect your new study link. This process takes a few minutes and occurs in the background. You can track the progress of this task, using the <a href=\"../../../getting-started-is/jobs\">job system</a>." %}
