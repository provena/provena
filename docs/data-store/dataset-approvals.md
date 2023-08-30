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

## (Dataset Reviewer) How to perform a dataset review

## Understanding approval history

## Who can review datasets?
