---
layout: default
title: Groups
nav_order: 7
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

# Groups overview

Provena provides the ability to define groups and access to grant access to resources in the Information System on a group-by-group basis. A group is simply a construct that is defined in the information system with a name and a set of users as members of the group. Each resource in Provena, e.g. a dataset, can then be configured to allow access to have read and/or write permissions. For example, a dataset on the Provena data store can be made available to one or more groups with differing levels of read/write access.

Currently groups apply to datasets in Provena. However, group access control functionality may be offered in other Provena components and resources in the future.

Refer to [Group admin ](./admin/groups.html) for how to add and manage groups. You will need to have an activated user account on Provena with the admin role assigned as a pre-requisite to creating/managing groups.

Once the group is created, users with admin roles for the dataset can add and manage group level permissions and access control. Refer to this guide for instructions: [Group access and configuration for datasets in the Data Store](./provenance/registry/access-control.html#group-access)

