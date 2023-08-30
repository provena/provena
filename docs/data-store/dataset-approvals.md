---
layout: default
title: Dataset Approvals
nav_order: 17
parent: Data store
---

{: .no_toc }

# Dataset Approvals

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Overview

The Provena Data Store enables users to request a review of dataset's for which they have [Admin Access](../registry/access-control#access-control-overview). The user who will perform the review must be selected from a fixed list of Dataset Reviewers.

The purpose of a review will vary significantly between organisations - Provena is not prescriptive about what such a review could include. For example, a dataset review process might include:

-   Quality assurance (QA)
-   Scientific review (e.g. process review, peer review etc)
-   Standards validation (e.g. metadata standards, quality standards, documentation)
-   Approval for public release

Provena will ensure that approved datasets, or datasets pending review, are locked down, meaning that the uploaded files cannot be modified or deleted.

If there is a need to modify files during or after approval, there are two options:

1. [Create a new version](../versioning/how-to-version-in-data-store) of the dataset and modify the files in the new version, or
2. Contact a system administrator and discuss manual remediation

The lifecycle of a dataset during the review process is visualised below.

<!--
PlantUML Source:
---

@startuml

skinparam wrapWidth 150

state NOT_RELEASED ##[bold]
state PENDING ##[bold]03a9f4
state RELEASED ##[bold]2e7d32

NOT_RELEASED : The Dataset is not released
PENDING : A Dataset review is currently in progress
RELEASED : The Dataset has been approved and cannot be modified

[*] -> NOT_RELEASED : Create Dataset
NOT_RELEASED -> PENDING : Requested
PENDING -> NOT_RELEASED : Denied
PENDING -> RELEASED : Approved
@enduml
-->

|                                        Release Lifecycle                                         |
| :----------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/release_lifecycle.svg" alt="drawing" width="600"/> |

## (Dataset Owner) How to request a dataset review

### Prerequisites

-   You must have a registered dataset in the Provena data store. It should be complete (meaning there are no expected changes to the data), and ready for review. For help registering a dataset, see [registering a dataset](./registering-a-dataset).
-   You must have [Admin Access](../registry/access-control#access-control-overview) to the dataset (meaning you are either the owner, or have been granted equivalent access)

### Find and view your dataset

To begin, navigate to your dataset in the Provena Data Store. For help finding your dataset, see [discovering and viewing datasets](./viewing-a-dataset).

For example, you could search (1) for your dataset, and select it in the list (2).

|                                            Find Dataset                                             |
| :-------------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/request_find_dataset.png" alt="drawing" width="600"/> |

### View approval information

Once you are viewing your dataset details, you should validate the current status as "NOT_RELEASED" (1) and move to the approvals tab (2). If your dataset is in the "RELEASED" state, then your dataset is already approved and no action is required. If your dataset is in the "PENDING" state, then a review has already been requested. You can see [Understanding approval history](#understanding-approval-history) below for more information.

|                                            Approvals Tab                                             |
| :--------------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/request_approvals_tab.png" alt="drawing" width="600"/> |

### Submit for approval

After moving to the approvals tab, you can verify the approval status (1) and click "Submit for Approval" (2) to start the request process.

|                                            Request Approval                                             |
| :-----------------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/request_request_approval.png" alt="drawing" width="600"/> |

Doing so will open a new page, where you can select your Approver using the dropdown menu (1), and include any notes to assist the Approver in the review process (2). Once ready, click (3) to confirm your readiness to submit the request, and (4) to submit. If you want to cancel this process and return to the previous view, click (5) (noting that this information is not saved until submitted).

If your desired dataset reviewer is not available in the dropdown menu, please contact your system maintainer to have them added to the list. More information is available [below](#who-can-review-datasets).

<td>{% include warning.html content="The notes section can include standard text, including new lines and punctuation. Currently, non ASCII characters such as emojis, are not supported and may cause issues in email delivery. Please include plain text only."%}</td>

|                                            Request Details                                             |
| :----------------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/request_request_details.png" alt="drawing" width="600"/> |

After clicking submit, a popup will appear notifying you of a successful request. After a few seconds, you will be redirected to the approvals tab of the dataset.

|                                        Request Success                                         |
| :--------------------------------------------------------------------------------------------: |
| <img src="../assets/images/data_store/release/request_success.png" alt="drawing" width="600"/> |

### Await review response

### Request again if needed

## (Dataset Reviewer) How to perform a dataset review

### Prerequisites

## Understanding approval history

TODO process here

## Who can review datasets?
