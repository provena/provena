---
layout: default
title: Access Control
nav_order: 5
grand_parent: Information System
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

# Access Control Overview

This document will discuss the types of access controls available and then discuss the methods to apply these access controls through the Registry user interface.

## What access controls are available for resources?

Access control is applied through roles. Roles enable actions on a resource.

All resource types have three basic roles:

1. Metadata Read - grants permission to discover and view the resource metadata
2. Metadata Write - grants permission to edit the resource metadata
3. Admin - grants all roles and permissions and enables access to locks and access control

Some resource types have additional roles, namely Datasets:

1. Dataset Data Read - grants permission to download the dataset files
2. Dataset Data Write - grants permission to upload and modify dataset files

# Applying Access Controls

The aforementioned controls can be applied for individual resources by those who have administrative access to the resource. By default, this is the owner of the resource and Registry administrators.

Each resource specifies an access configuration. This configuration defines a set of access grants for a selection of groups. All resources must specify at least one set of access grants for the default "General Users" group, as defined below. Users can configure extra access grants for custom user groups as discussed below.

## Overview

### Finding resource settings

The resource settings (1) and access settings (2) (shown below) are only visible if you are a resource administrator.

|                                          Finding resource settings                                           |
| :----------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/finding_settings.png" alt="drawing" width="600"/> |

### Making and submitting changes

Access is configured by toggling sliders in the Granted column (1). Roles apply to a group. The general access group (2) (described below) is always visible. To modify access for a group, press the Add group '+' button (3) and select the group from the list. You can modify the roles granted to a group using the edit pencil icon (4). To remove access for a group, use the 'x' button next to the pencil edit icon (4).

|                                              Access controls                                              |
| :-------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/access_layout.png" alt="drawing" width="600"/> |

Once a change is detected, you will see a popup appear at the top of the page. You can press "Submit Changes" to lodge this change, or "Revert Changes" to restore the access configuration to it's prior state. Once submission is completed the page will automatically refresh with the updated access configuration.

{% include warning.html content="No changes will be saved to the access configuration until the submit button is pressed." %}

## General user access

### Who are general users?

The "General Users" group contains all users of the Registry. Each resource must specify a set of access grants for this group. This could range from no access (non discoverable and non accessible), to complete access.

When a new resource is created, the General Users group is assigned only metadata read permission. This configuration can be modified using the processes detailed below.

{% include notes.html content="Datasets also receive the General User 'Dataset Data Read' role by default." %}

### Where to manage general user access

Upon registering a resource, the general Registry user access rights can be managed by navigating to the 'settings' tab when viewing the resource. The general access roles can be modified by using the toggle sliders under the "General Access" heading - as shown previously.

## Group access

If configuring access for all users does not provide enough control, a resource administrator can configure access grants on a group-by-group basis. Configuring access for a group grants this access to all registered members of the group.

A resource can be made available to more than one group with differing accessibility levels (see note below). For example, you may wish to have a group of resource contributors which will require write access, and another group for resource viewing only, meanwhile the more general system users may not have access at all.

{% include notes.html content="If a user is accessing a resource which has access rules for multiple groups of which the user is a part of, the user will be granted the most permissive combination of those access rights" %}

### Adding group access to a resource

You can grant group access to a resource you have administrative control over by viewing the resource, navigating to the settings panel (1), expanding the Access Control section (2), and selecting "+ Add Group" (3), as highlighted below.

|                                              Adding groups                                               |
| :------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/adding_group.png" alt="drawing" width="600"/> |

The resulting popup will allow you to select from the created groups. If you only want to show groups you are in, select the toggle button (1). If you can't see the group you are looking for, you may need to visit the next page (2). Select one or more groups by clicking on the row(s), and pressing submit (3).

|                                           Submitting selected groups                                            |
| :-------------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/adding_groups_panel.png" alt="drawing" width="600"/> |

Once the selected groups are added, you will see a row for each group in the Group Access subsection. By default, each group is configured with no roles. To change the access configuration for a group, press the "Edit" pencil icon in it's row (1) and use the toggles on the resulting popup to grant access.

|                                              Configuring group access                                              |
| :----------------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/selecting_group_access.png" alt="drawing" width="600"/> |

### Remove Group Access

To remove the access grants for a group, remove the group using the "x" icon (1). This will not delete the group. Make sure to submit your changes!

|                                             Removing a group                                             |
| :------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/remove_group.png" alt="drawing" width="600"/> |

### Creating a group

Group creation is currently performed by Information System Administrators. For help requesting a group, see [groups](../../groups).

### Group Access typical dataset configuration examples

The below screenshots will highlight some common access configurations for dataset resources.

If you would like all registry users to be able to view and download your dataset, but not edit the contents of it,
grant general user read access for both metadata read and dataset read:

|                        Enabling general user read access to dataset metadata and data                         |
| :-----------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/general_user_read.png" alt="drawing" width="600"/> |

Furthermore, if you'd like to limit the editing rights to a group of team members, you can create an editors group and enable
write permissions for them whilst leaving the general user write permissions (for metadata and data) _not_ granted.

|                                        Editors group dataset access                                         |
| :---------------------------------------------------------------------------------------------------------: |
| <img src="../../../assets/images/data_store/access_control/dataset_editors.png" alt="drawing" width="600"/> |

If at some point you wish to temporarily disable all updates/writes to the dataset, it may be easier to apply a [resource lock](./resource_lock) as opposed to the potentially more complex task of managing the group/user roles.
