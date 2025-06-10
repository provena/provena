---
layout: default
title: Create/Manage Groups
nav_order: 8
parent: Admin tools
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

# Create/Manage Groups

This page documents how to administer [Groups](../groups) in a Provena server in order 
to [manage access](../registry/access-control). 

Groups are defined with a name and a set of users as members of the group. 
Groups can then be used in configuring access control to have read and/or write 
permissions on a resource. 

Currently groups apply to datasets in Provena. However, group access control functionality may be offered in other Provena components and resources in the future.

You will need to have an activated user account on Provena with the admin role assigned as a pre-requisite to creating/managing groups.

## Create a group

Navigate to the Provena landing portal.

|                           Provena landing portal                                 |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_1.png" alt="drawing" width="500"/> |

Click on the "Admin" link in the top navigation bar. You will need to have logged in as a user with the admin role. This will bring up the "Admin Console"

|                           Provena Admin Console                                  |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_2.png" alt="drawing" width="500"/> |

Click on "Group management".

|                           Group management console                               |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_3.png" alt="drawing" width="500"/> |


Click on the "+" button. 

Add group details including the ID (which must be unique), display name and a group description. 

|                              Add Group Dialog                                    |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_4.png" alt="drawing" width="500"/> |


Click on the "Submit" button to add the group. The group will now appear in the Group Management section of the Admin Console.

|                          Group added and listed                                  |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_5.png" alt="drawing" width="500"/> |

## Add users to a group

Select the group in the Group Management section of the Admin Console. Once selected, click on the "Add member" button. 

|                             Add member in Group admin console                    |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_6.png" alt="drawing" width="500"/> |


Add details for the user to add. The username must match with the user to be added. You can fill in the other fields optionally. In future, this information may be retrieved from the Provena server if known. For now, this is manually entered/updated.

|                           Add user to group  dialog                              |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_12.png" alt="drawing" width="500"/> |

The user will be listed in the Users table in the Group admin page.

|                            User added to group                                   |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_13.png" alt="drawing" width="500"/> |

Additional users can be added with this flow. The figure below shows an update list of users in the 
Users table in the Group admin page.

|                         Other users added to group                               |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_14.png" alt="drawing" width="500"/> |


## Manage group

## Update group metadata

You can update the group metadata by clicking on "Update group" in the Group admin page. This provides the option for updating the Display name or Description.

|                                 Update group info                                |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_15.png" alt="drawing" width="500"/> |


## Update user membership

Users can be added or removed from the group using the "Add member" and "Remove members" button. 

To remove users, select the checkbox for the user and click on the "Remove members" button. 

|                            Remove members                                        |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_17a.png" alt="drawing" width="500"/> |

Confirming will remove the users from the group.


|                            Confirm remove members                                |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_17.png" alt="drawing" width="500"/> |



## Delete group

Click on the "Delete group" button. 

|                                 Delete group                                     |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_16a.png" alt="drawing" width="500"/> |

Confirming this will delete the group.

|                            Confirm delete group                                  |
| :------------------------------------------------------------------------------: |
| <img src="../assets/images/admin/admin_group_16.png" alt="drawing" width="500"/> |


