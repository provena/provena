---
layout: default
title: Registering a dataset
nav_order: 3
grand_parent: Provena
parent: Data store
---

{: .no_toc }

# Registering a dataset

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Registering a dataset
Users start the dataset registration process by logging into Provena. They then select **Data Store** from the side menu  

|                                Selecting Data Store from menu                           |
| :-------------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/selectDataStoreFromMenu.png" alt="menu_button" width = "200"/> |


then they click on the **Register Dataset** button.


|                                 Registering a dataset                                    |
| :---------------------------------------------------------------------------------:      |
| <img src="../../assets/images/data_store/registerDataset.png" alt="drawing" width="600"/> |


When registering a dataset with Provena's Data Store you are initially required to complete a metadata record. The inputs requested are listed below, make sure you have these prior to filling out the form. After submitting, the system generates a persistent unique identifier that can be used similarly to a Digital Object Identifier (DOI). The generation of metadata records will facilitate the sharing and discovery of data.

___
### Filling out form fields
User entered metadata fields are listed below, some of which are pre-populated, others are selected or searched for with the help of form widgets. 

{% include_relative user-metadata-fields.md %}

<br>

#### Auto generated metadata fields

After you **Submit** the newly registered dataset, Provena will mint a **Handle** and allocate a directory in the Provena online data storage. The **Handle** identifier and data directory path will be included in the metadata record.

{% include_relative generated-metadata-fields.md %}

___
### Missing fields

After clicking **Submit** if a mandatory/**required** field is not given a popup will appear indicating that important information is missing.

You will not be able to progress unless all required fields are entered.

___
### Usage licence

You can attribute the appropriate licence from the dropdown list. There are ten licences to choose from. For details of each licence please see the [Licenses](../licenses.md){:target="\_blank"} page.

___
### What happens during the minting dataset process?

A Handle Identifier is minted with each dataset that is registered and will associated with the dataset metadata. This minted identifier can be used to persistently locate the dataset in the future. See [Digital Object Identifiers](../digital-object-identifiers.md){:target="\_blank"} for further details.

___
## File types and maximum file size

The Provena Data Store can store a variety of data files e.g. text, csv, netCDF, word documents, images, video etc... Users can upload files or folders using either the AWS web console (GUI), AWS command line interface (AWS CLI) or a program like [WinSCP](../data-store/WinSCP-data-access.md){:target="\_blank"}.

While the AWS CLI can handle large files (>100GB) and the AWS Console GUI can handle up to 160GB uploads, please contact the Provena team if you know you will be uploading large or numerous files. For technical information about the storage limitations of the S3 service (which the data store is built on) you can review the AWS FAQ [here](https://aws.amazon.com/s3/faqs/#:~:text=How%20much%20data%20can%20I%20store%20in%20Amazon%20S3?){:target="\_blank"}.

The maximum file size that can be uploaded is 5TB.  
To upload files, see [Uploading a dataset](../data-store/uploading-a-dataset.md){:target="\_blank"}.