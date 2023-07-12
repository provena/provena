---
layout: default
title: Registering an Entity
nav_order: 2
has_children: false
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

# Registering an entity

**Link**: [https://registry.mds.gbrrestoration.org/registerentity](https://registry.mds.gbrrestoration.org/registerentity)

## Required Permissions

-   Registry Read
-   Registry Write

## Process

### Step 1. Navigating to the Register Entity page

From the home page of the Registry, click the "Register a new entity" button, as shown below:

|                                   Register a new entity                                   |
| :---------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/register_start.png" alt="drawing" width="800"/> |

### Step 2. Selecting an Entity Type

At the top of the page, you can select the entity type from the dropdown. Simply click on the dropdown and click on the desired type:

|                                   Select an entity type                                    |
| :----------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/register_select.png" alt="drawing" width="800"/> |

### Step 3. Filling out the form

Once you have selected your entity type, the updated form will load.

Form fields will provide guidance on what is expected underneath the input field, for example:

|                                      Form caption                                       |
| :-------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/form_caption.png" alt="drawing" width="800"/> |

Form fields can be of various types:

-   **Text**: Text fields are either single or multi line input boxes. Simply click inside the box and type the desired text.
-   **Selection**: Some fields allow selection from a predefined list of inputs - click the dropdown and select the desired item from the list.
-   **Yes or No**: Yes or no (boolean) fields are displayed as a check-box. To indicate "yes" or "true", tick the box. Otherwise, leave the box unticked.
-   **List**: Some fields contain a list of items. To add an item to the list, use the "+ Add Item" button. To remove the item, use the "-" button on the right hand side. Both buttons are shown below.

|                                      Add item                                       |
| :---------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/add_item.png" alt="drawing" width="800"/> |

|                                      Remove item                                       |
| :------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/remove_item.png" alt="drawing" width="800"/> |

-   **Other Entities**: Some entity types require references to other registered entities. To help this process, the form allows you to search for resources of a specific type based on their properties. You can search by name, ID, or other fields. For example, when registering a "Model Run Workflow Template" you can select a model by typing a search query into the input field, selecting your desired result, and clicking it in the list. To clear your selection, use the "Clear Selection" button that appears after selection.

|                                      Selecting other entities                                       |
| :-------------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/selecting_other_entities.png" alt="drawing" width="800"/> |

### Step 4. Submitting the form and handling errors

Once you have completed the form, use the "Submit" button at the bottom of the page to register the entity.

If there were no validation errors in the form, you will receive a success alert:

|                                      Form success                                       |
| :-------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/form_success.png" alt="drawing" width="800"/> |

If there were form validation errors, or another issue occurred, you will see an error indication either on the field itself (such as when a field is not completed), or at the top of the page (when more detailed validation catches an error after submission). In this case, the format of the URL did not include the required "https" component, so an error appeared on the field:

|                                      Form error                                       |
| :-----------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/form_error.png" alt="drawing" width="800"/> |

After correcting the issue, the submit button can be pressed again - it is safe to repeat this process until the form is accepted.

# Updating an entity

## Required Permissions

-   Registry Read
-   Registry Write

## Process

Updating an entity is a very similar process to registering an entity, except that the existing form details are pre-filled from the record.

Start by navigating to the entity (see [exploring the registry](./exploring-the-registry.html) for more information). From the entity detailed view, you can select "Edit Entity" on the right hand side:

|                                          Edit                                          |
| :------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/edit_button.png" alt="drawing" width="800"/> |

When updating a registered entity, you will need to provide a reason for performing the update. This reason is documented and helps to understand how a resource may have changed over time, and why. Enter your reason in the text field as highlighted below (1).

|                                      Updating reason                                       |
| :----------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/updating_reason.png" alt="drawing" width="800"/> |

Then make the desired changes to the record on the resulting form, clicking submit when you are ready to publish the updates. For help completing these forms, see [registering an entity](#registering-an-entity) above.

If Submit button is greyed and you cannot submit then please double check you have entered a reason for the update, as mentioned above.

|                                      No reason provided                                       |
| :-------------------------------------------------------------------------------------------: |
| <img src="../../assets/images/registry/no_reason_provided.png" alt="drawing" width="800"/> |
