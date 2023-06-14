---
layout: default
title: Downloading a dataset
nav_order: 7
grand_parent: Information System
parent: Data store
---

{: .no_toc }

# Downloading and synchronising datasets

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Prerequisites

Without taking some initial steps, data that other users share with you won't be visible nor accessible. Data cannot be shared directly using the AWS S3 storage backend as access is provided through our system.

Ensure you have followed the below steps before attempting to download data from the RRAP M&DS IS data store.

___

### Appropriate access

In order to **download** data you need to have **read** access for the data store. See [requesting access](../getting-started-is/requesting-access-is.html){:target="\_blank"} for information on how to request access.

{% include notes.html content="If you are also intending to upload data, you should request access to the 'write' level for the data store, as well as 'write' access to the handle service. The levels of access required for common sets of operations is described in more detail in the link above." %}

___
### AWS CLI installation

Downloading data is possible using only the AWS web console, however the features are very limited (in particular, you can only download one file at a time). We recommend and will focus on supporting the usage of the AWS CLI v2. Instructions on how to install this easy to use tool are available [here](setting-up-the-aws-cli.html){:target="\_blank"}.

___
## Finding the dataset

In order to download a dataset, you must first identify it on the system. Once you reach the listing for that dataset in the data store, tailored instructions on how to download that dataset will be generated for you, making downloading a very quick process.

___
### Using the registry

Once you open the [data store](https://data.rrap-is.com){:target="\_blank"} and log in, you can navigate to datasets using the banner at the top and use the listing, filtering and searching functionality to locate the desired dataset to download. Select the dataset you wish to view and download from the list.

{% include notes.html content="Currently the search functionality of the data store is not complete and will only select exact text matches." %}

___
### Using a shared link

The [persistent identifier](../digital-object-identifiers.html){:target="\_blank"} generated when a dataset is minted can be shared in a special form to enable one click persistent navigation to that dataset. If someone shares a M&DS data store link with you, you will be navigated to the dataset listing directly. You can follow on with the instructions below once you have reached the dataset listing.

___
## Downloading files

Once you select the dataset you want to download, you can click the entry and you will be redirected to a view of the dataset. This view shows three options _preview_, _download_ and _upload_. After using the preview section to view information about the dataset, you should choose the _download_ option.

Doing so will provide you with detailed instructions on how to download the dataset.

___
### First time download (`aws cp` command)

If you have not downloaded this dataset before, you can use the provided AWS CLI commands to download the files.

Ensure that you create a new folder on your system, and navigate (using the terminal environment in which your AWS CLI tool is installed) to the location containing that folder. You will also need to use the 'Generate Credentials' button in the data store to produce temporary access credentials. The data store provides the commands to set the required [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html){:target="\_blank"} which enable access to the data. Be sure to choose the format which suits your terminal environment.

The data store provides a command ready to copy and paste - you will just need to change the name `folder` to suit the name of the folder you created.

If you have issues following these instructions, please don't hesistate to contact the M&DS IS team for more detailed assistance.

___
### Updating local files from updated dataset (`aws sync` command)

The AWS CLI provides more than one option for copying data from a bucket to your local machine. The `cp` command above assumes that you don't have any of the files on your local machine. The `sync` command will only download **new files** or **files that have changed**. This means that if only some of a dataset is updated, you don't need to download it all again. For more information about how the sync command works, please see the official [AWS documentation](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html){:target="\_blank"}.

{% include notes.html content="Files that exist locally which have been removed from the dataset will not be deleted locally. To enable this optional behaviour, you can use the --delete flag. Please use with caution as improperly using this option (for example, if you are in the wrong working directory in your AWS CLI terminal environment) could cause significant damage to your local filesystem." %}

To use the sync operation, replace `cp` with `sync` in the generated copy command. Also remove the `--recursive` option. Remember you will need to have active AWS credentails to run this command. For example:

```
aws s3 sync s3://<provided path here> local_folder
```
