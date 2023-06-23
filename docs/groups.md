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

# Requesting a new group

If you would like a new group, you will need to send request for a new group to be added.

Step 1. To request a new group, please submit a request via the Provena Issues tracker via this link:
[https://github.com/provena/provena/issues](https://github.com/provena/provena/issues)

Step 2. Click on the **New Issue** button to initiate a request issue (see screenshot below).

|                       Request a group via the Github issue tracker                        |
| :---------------------------------------------------------------------------------------: |
| <img src="../assets/images/provena-request-a-group-issue-create.png" alt="drawing" width="600"/> |

Step 3. Add details for the request for a new group (see screenshot below). It would be useful to add the group name in the issue title. In the body of the issue, edit the text to describe
the group, and any additional context. For example, this might include a list of members needed in the group.

|                              Add details for group request                               |
| :--------------------------------------------------------------------------------------: |
| <img src="../assets/images/provena-request-a-group-issue-create-step2.png" alt="drawing" width="600"/> |

Step 4. Click the **submit new issue** button.

Once submitted, a notification will be sent to the Provena team, who will administer the request. You will be contacted to confirm details for the group.

Once the group is created, you may use it in the information system.

## Related pages

[Group access and configuration for datasets in the Data Store](./provenance/registry/access-control.html#group-access)
