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

## Overview of the process

The diagram below outlines the steps undertaken when registering and uploading a dataset.

![Workflow diagram](../../assets/images/DRAFTv2_upload_data.png)
_A User logs into the RRAP information system & selects DATASTORE then REGISTER DATASET from the website. A metadata form prefilled with the User’s name & email address opens and the User fills out information relating to the data being uploaded (see [Filling out form fields](#filling-out-form-fields){:target="\_blank"} for more detailed information). After the metadata form is completed the User uploads the dataset by one of these [methods](../data-store/uploading-a-dataset.md#Uploading-dataset-files){:target="\_blank"}, depending on the size of the file(s). The data is assigned its own unique PID (Persistent Identifier). The data is securely stored on an AWS S3 server, ready for future reference and usage._
<br>

___
## Registering a dataset
Users start the dataset registration process by logging into the RRAP M&DS Information System. They then select **Data Store** from the menu <img src="../../assets/images/data_store/hamburgerMenu.png" alt="menu_button" width = "20"/>, then they click on the **Register Dataset** button.  

|                                 Registering a dataset                                    |
| :---------------------------------------------------------------------------------:      |
| <img src="../../assets/images/data_store/registerDataset.png" alt="drawing" width="600"/> |


When registering a dataset with the RRAP-IS Data Store you are initially required to complete a metadata record. The inputs requested are listed below, make sure you have these prior to filling out the form. After submitting, the system generates a persistent unique identifier that can be used similarly to a Digital Object Identifier (DOI). The generation of metadata records will facilitate the sharing and discovery of data.

___
### Filling out form fields
User entered metadata fields are listed below, some of which are pre-populated, others are selected or searched for with the help of form widgets. 

{% include_relative user-metadata-fields.md %}



<br>
If you know an individual or organisation's Research Organisation Registry number (ROR) you can use the **Manual override** button to manually enter it in.

|                               Using the manual override                                   |
| :---------------------------------------------------------------------------------:      |
| <img src="../../assets/images/data_store/metadataOrganisationROR.png" alt="drawing" width="600"/> |


<br>
The ROR has been selected when you can see you can use the publisher name and publisher ROR appear above the search bar. A **clear selection** button will also appear. You can use this if you have made a mistake and need to re-enter the publisher's information.

|                               ROR selected                                   |
| :---------------------------------------------------------------------------------:      |
| <img src="../../assets/images/data_store/metadataOrganisationRORSelected.png" alt="drawing" width="600"/> |

<br>

#### Auto generated metadata fields

After you **Submit** the newly registered dataset, the RRAP-IS system will mint a **Handle** and allocate a directory in RRAP-IS online data storage. The **Handle** identifier and data directory path will be included in the metadata record.

{% include_relative generated-metadata-fields.md %}

___
### Missing fields

After clicking **Submit** if a mandatory/**required** field is not given a popup will appear indicating that important information is missing.

You will not be able to progress unless all required fields are entered.

___
### Usage licence

You can attribute the appropriate licence from the dropdown list. There are ten licences to choose from, although all data produced by RRAP is by default attributed Copyright 'All rights reserved'. For details of each licence please see the [Licenses](../licenses.md){:target="\_blank"} page.

___
### What happens during the minting dataset process?

A Handle Identifier is minted with each dataset that is registered and will associated with the dataset metadata. This minted identifier can be used to persistently locate the dataset in the future. See [Digital Object Identifiers](../digital-object-identifiers.md){:target="\_blank"} for further details.

___
## File types and maximum file size

The M&DS IS Data Store can store a variety of data files e.g. text, csv, netCDF, word documents, images, video etc... Users can upload files or folders using either the AWS web console (GUI), AWS command line interface (AWS CLI) or a program like [WinSCP](../data-store/WinSCP-data-access.md){:target="\_blank"}.

While the AWS CLI can handle large files (>100GB) and the AWS Console GUI can handle up to 160GB uploads, please contact the RRAP M&DS IS team if you know you will be uploading large or numerous files. For technical information about the storage limitations of the S3 service (which the data store is built on) you can review the AWS FAQ [here](https://aws.amazon.com/s3/faqs/#:~:text=How%20much%20data%20can%20I%20store%20in%20Amazon%20S3?){:target="\_blank"}.

The maximum file size that can be uploaded is 5TB.  
To upload files, see [Uploading a dataset](../data-store/uploading-a-dataset.md){:target="\_blank"}.