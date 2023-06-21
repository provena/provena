---
layout: default
title: Setting up the AWS CLI for download and upload
nav_order: 12
grand_parent: Provena
parent: Data store
---

{: .no_toc }

# Setting up the AWS CLI for download and upload

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Background

### What is the AWS CLI?

The AWS CLI is a tool developed by Amazon Web Services (AWS) to enable programmatic access to resources deployed in AWS Cloud Computing environments.

### How does Provena use this tool?

Provena uses AWS Simple Storage Service (S3) to store dataset files. This means that the AWS CLI is a very useful and mature tool which can help Provena provide reliable, efficient and powerful access into the data store. In order to upload large or numerous files we recommend using the AWS CLI as it is faster than using the online AWS console (web GUI). The AWS console only allows the download of individual files meaning that downloading many small files in a dataset is also better served through the CLI. 

### How will I know what commands to use?

While there is extensive online documentation about using the AWS CLI, where possible we will provide dynamically generated commands which you can copy and paste into your terminal environment to execute AWS CLI commands which will download, upload or list data.


### How does Provena provide secure access to these files?

Provena uses single sign on to identify users. Users which have appropriate role permissions (see [requesting access](../getting-started-is/requesting-access-is.html){:target="\_blank"} for more information) will be able to use their Provena identity token to generate AWS credentials on demand. The data store and other systems will provide credentials as you require them for download and upload operations.

## Installing the AWS CLI v2

The instructions below are based on the AWS instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){:target="\_blank"}. You should visit this guide if you require more instructions.

### Windows

If you have an existing AWS CLI installation, it can be used as long as it is up to date. If you have an existing installation but it is not up to date, you should remove it first by following the Uninstall AWS CLI version 1 heading of [these instructions](https://docs.aws.amazon.com/cli/v1/userguide/install-windows.html){:target="\_blank"}. 

Assuming now that you have no pre-existing version of the AWS CLI, you can download this [installer](https://awscli.amazonaws.com/AWSCLIV2.msi){:target="\_blank"}. 

Once you run this installer, open the command prompt by using the start menu and selecting cmd. If you execute `aws --version` in the cmd terminal, you should not receive an error and the version number (2.x.x) should be printed out.

While the command should be in your path by default, you may need to follow [these instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-path.html){:target="\_blank"} if it isn't.

### Linux

If you have a pre-existing installation of AWS CLI, it can be used as long as it is up to date. If it is not, you should uninstall it first by following the uninstall instructions [here](https://docs.aws.amazon.com/cli/v1/userguide/install-linux.html){:target="\_blank"}. 

Assuming that you have no existing installation, you can run the following commands in a bash terminal: 
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
For more detailed instructions, visit the linux section of this [documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){:target="\_blank"}. 

Once the install executes, you should be able to run the `aws --version` command in your preferred bash terminal. This command should have no errors and should print out a version number (2.x.x).
