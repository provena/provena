---
layout: default
title: Overview
nav_order: 1
parent: Data store
grand_parent: Information System
---

{: .no_toc }

# Data Store Overview

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

All datasets that are inputs or outputs for operational products must be registered and stored on the RRAP information system. It is expected that (but not essential) that the registration and storage will occur concurrently. The metadata required for each dataset is to be determined during workshop by the sub-program teams. It is expected that metadata will consist of 3 types of information:

-   Disciplinary (science) based metadata which will describe aspects of the data relevant to the research community.
-   Program based metadata containing key information from a program perspective.
-   Provenance metadata which will most likely include a unique identifier for the dataset, and a reference to the identifier of the process used to generate the dataset.

The Data Store facilitates registration and creation of datasets for RRAP M&DS. Uploaded data is stored in an AWS S3 bucket, which serves as a persistent storage repository.

|                                      Simple Data Store                                      |
| :-----------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/Data_Store_simple.jpg" alt="drawing" width="600"/> |

## What can users do in the Data Store?

Users can now login to the RRAP M&DS Data Store to do the following.

[**Register datasets**](./registering-a-dataset.md){:target="\_blank"}: Create a dataset record for a dataset relevant to M&DS. Dataset records could either point to a dataset that is managed externally (e.g. institutional repositories) or a location in the M&DS Data Store. Valid examples of dataset records include:

-   CSV files
-   a set of related NetCDF files

[**Upload files**](./uploading-a-dataset.md){:target="\_blank"}: Authorised users are able to upload files to a location registered in the Data Store. When a user registers a dataset, a digital identifier is minted for that dataset and a folder is created in the shared AWS S3 bucket. Users can then upload files to that location via AWS S3 tools. Learn more about RRAP M&DS IS Digital Identifiers here.

[**Discover datasets**](./viewing-a-dataset.md){:target="\_blank"}: Authorised users can access the Data store to search for datasets and view their details.

[**Download and synchronise datasets**](./downloading-datasets.md){:target="\_blank"}: Authorised users are able to access files on the Data Store and download them to a local computing environment using AWS tools and the AWS web console. Users can also synchronise dataset folders to a local computing environment, which only downloads updated files optimising file transfer. This will allow users to share data and synchronise data updates.

**Automated archival**: Datasets that are registered and uploaded to the Data store will be archived using automation tools. Archival will allow RRAP to manage these datasets for future reference.

Browse to the [IS Landing Page](https://mds.gbrrestoration.org/){:target="\_blank"}
