---
layout: default
title: FAQ
nav_order: 9
---

{: .no_toc }

# Frequently asked questions (FAQs)

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Access

### How do I request access to the data store?

You should make a user access request by visiting the [landing portal](./getting-started-is/requesting-access-is) and pressing your profile (user silhouette in the top right) then choosing Roles. Information about how to use this menu and which roles you should request is available at [request access](./getting-started-is/requesting-access-is.html){:target="\_blank"}.

### How do I get a Provena AWS account?

If you have logged in to Provena and have requested the appropriate roles then you are setup and ready to access protected AWS resources. Users of Provena do not directly possess or own AWS accounts, rather we broker temporary credentials on your behalf as an authorised user of the system. When undertaking actions that require AWS access credentials, they will be generated automatically for you. For information about logging in see [logging in](./getting-started-is/logging-in.html){:target="\_blank"}. For information about requesting access see [requesting access](./getting-started-is/requesting-access-is.html){:target="\_blank"}.

## Datasets

### How do I find a dataset someone else has uploaded?

Firstly, ensure that you have [logged in](./getting-started-is/logging-in.html){:target="\_blank"} and have requested data store [access](./getting-started-is/requesting-access-is.html){:target="\_blank"} (at least read level). You can now visit the [data store](./data-store/index.html), login and select Datasets from the banner. From this menu, you will see a list of registered datasets. You can search this list (noting that the search functionality is currently limited) and filter by organisation. Once you have selected the dataset you wish to view, you can click it in the list. From here, there are instructions on how to [view this dataset](./data-store/viewing-a-dataset.html){:target="\_blank"} or [download the files](./data-store/downloading-datasets.html){:target="\_blank"}.

### How do I find datasets that have been uploaded by my organisation?

By following the above procedure, you will have access to the list of datasets in the [data store](./data-store/index.html). You can filter by organisation using the clickable tick boxes in the left panel.

### Can I upload data on behalf of someone, as I'm not the owner of the data?

In some cases, it might be useful to republish a dataset in the Provena for various reasons, e.g. automation, and long term storage of important data.
For this reason, users can upload other people's data as long as they have permission or rights to republish that data. It may be useful to add this information to the dataset (e.g. written permission in an email attachment file, or description of details in the README file).

### My computer crashed while uploading the data - how do I see what was loaded?

The answer to this question depends on how far you made it before the big bang. If you successfully [registered the dataset](./data-store/registering-a-dataset.html){:target="\_blank"} then the entry exists in the registry and upload can be resumed. If you did not complete registration, you will need to start the process again. Once an entry exists (through registration), you can add files to it at any point by visiting the entry in the [data store](./data-store/index.html). After registering the dataset you may also like to take note of the handle link so that you can easily get back there later. If you were in the middle of uploading files when a crash occurred, you can use the instructions on the 'upload' tab of the dataset view in the data store as required to continue the upload. To view what's there you can use the AWS console GUI or the `aws s3 ls` command. If you want to resume your upload using the GUI you will need to assess what uploads were complete and choose the remaining files to upload (or simply upload the whole dataset again, noting that this will require uploading all the files again). If you used the AWS CLI, then you will be able to use the same `aws s3 sync` command again (the `s3 sync` command **will not upload the same data if it hasn't changed** meaning that your upload will be safely resumed). For this reason (and others) we would recommend using the AWS CLI for large datasets, and particularly for large datasets with numerous files.

### I have new data to add to a data set, how do I go about this?

To add new data to a dataset you must first have write permissions into the data store - for more information on permissions you can visit [requesting access](./getting-started-is/requesting-access-is.html){:target="\_blank"}. Once you have the appropriate permissions, you should locate the dataset. You can do this by visiting a shared [handle](./digital-object-identifiers.html){:target="\_blank"} link or by using the dataset search/listing functionality in the [data store](./data-store/index.html). Once you have found the dataset you wish to modify, select the 'upload' tab of the dataset view. You can then choose to upload files using either the AWS Web Console (first option) or the AWS CLI (second option). For more detailed information about how these upload processes work see [uploading](./data-store/uploading-dataset-files.html) and [setting up the AWS CLI](./data-store/setting-up-the-aws-cli.html){:target="\_blank"}. If you use the AWS web console, simply follow the normal steps to upload data, choosing your additional data. If you use the CLI, you can run the usual sync command from the same directory and **only the new files will be uploaded**. For more information about how the AWS CLI sync command works, see [aws sync](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3/sync.html){:target="\_blank"}.

<td>{% include notes.html content="If you use the CLI, you can run the usual sync command from the same directory and <b>only the new files will be uploaded</b>. For more information about how the <a href='https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html'>AWS CLI sync command works</a>"%}</td>

### Can I add to someone else's dataset?

Using the [groups](groups.html) feature, users may be granted write access to a dataset belonging to another person. The registrant of the dataset would need to specify a group, and grant it write access (e.g. Group A).
The group would need to specify the required members to be added as users in the group (e.g. Mary in Group A).
If this is configured correctly, the user (e.g. Mary in Group A) will be able to access the dataset as an editor and [upload files to the dataset](./data-store/uploading-dataset-files.html).

### How do I share my dataset?

You can share your dataset with others by using the handle link. See [Collaborating](./data-store/viewing-a-dataset.html#collaborating){:target="\_blank"} for more information.

## Versioning


### Why would I need a new version?

* You would like to create a new version of the item as an update because the previous item is now deprecated or erroneous, e.g. a updated model software or an updated dataset
* You would like to maintain two versions of an item which are both valid and in use but have different lineages and applications


A reason a user registers new versions of a model could be to to precisely describe which model version was used in a workflow. This can be useful for supporting repeating model runs or data reproducibility (i.e. re-running specific versions of a model software in a workflow specification).

### What's the difference between a version and metadata history?

Metadata history is a lightweight change tracking mechanism (typos, metadata corrections). Reasons for updating metadata:

-   Adding a citation
-   Minor updates to the description or the title of the item (e.g. dataset, model)
-   Corrections of minor errors (e.g. typos, missing information) which do not constitute a significant change in the utility or purpose of the item

Versioning an item creates a new entity in Provena. This includes the minting of a new identifier and new entity that is linked to the previous version of the item. It gives users the ability to signal that there is a new version of a thing. Reasons for a new version could be:

No - Provena doesn't allow creating a version from a previous version, i.e.  version branching. This would raise issues such as merge conflicts. Therefore, this is currently out of scope.

### Are users able to create a version from a non-current version, rather than the latest?

No - Provena doesn't allow creating a version from a previous version, i.e. version branching. This would raise issues such as merging, dangling branches, etc. This feature is intentionally excluded to prioritise a simple, understandable lineage of item versions.

Provena implements a simple versioning scheme where versions are created from the latest version.

### What's the difference between the 'clone' feature and the 'versioning' feature?

Functionality wise, the clone and versioning feature looks similar - metadata is copied, and a new identifier is minted for the item. 

The difference between "clone" and "versioning" is that for a new version:
- the new versioned item is linked to the previous version of the item by a version activity in the provenance graph

### What happens when a version is created for Datasets?

When a new version is created for a Dataset and if users want to use the Provena data storage feature, a new storage location is created. This storage location will be empty for users to upload relevant data for that version.

Other things that happen when a version is created:
- The new versioned dataset is linked to the previous version of the dataset
- A version activity is generated in the provenance graph linking the versioned dataset with each other
- Both versions of the dataset contain information in their metadata which the user can view to see the links to previous/next versions. Both are managed independently of each other

### Why can't I create a version for this item in the Registry?

To be able to version an item in the registry, you will need:
- to ensure you are logged in and have Admin permissions for the item
- to ensure you have navigated to the latest version of an item in the Registry
- to ensure the item is an allowable type to be versioned (see below)

#### What can be versioned?

All registered items which are in the _Entity_ category, can be versioned. For more information about the categories of registered items, see the [provenance overview](../provenance/overview/what-are-entities).

This includes:

-   Dataset
-   Model
-   Dataset Template
-   Model Run Workflow Template

#### What cannot be versioned?

_Agents_ and _Activities_ cannot be versioned, this includes:

-   Person
-   Organisation
-   Model Run

## Support

### How do I log a fault?

In all of Provena web pages there is a button on the right side of the page; "Contact Us". Pressing this button will show a structured form you can fill out to report an issue to the development team. Please include as much pertinent information as you can to help us quickly identify and resolve the issue. We will contact you via the email provided as the status of the issue changes.


