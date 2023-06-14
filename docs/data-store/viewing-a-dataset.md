---
layout: default
title: Viewing a dataset
nav_order: 6
grand_parent: Information System
parent: Data store

---
{: .no_toc }
# Viewing a dataset
<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

## Viewing a dataset
Users can view a dataset a number of ways once they are logged into the RRAP M&DS Data Store.

- Using the **Browse datasets** link under the under the **Find out more** menu.
- Entering information, such as the dataset name, in the **Search Dataset** field and clicking the magnifying glass button

|                                     Browse datasets                             |
| :-----------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/viewDataset.png" alt="drawing" width="600"/>      |

Users are then taken to the Datasets page.

|                                     Datasets page                               |
| :-----------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/viewDataset2.png" alt="drawing" width="600"/>     |


On this page, Users can quickly filter datasets by organisation by selecting the check boxes beside each name. Once you have found the dataset you are looking for, click on the dataset name and you will then be taken to the dataset's metadata page.

|                                   View Dataset metadata view                     |
| :------------------------------------------------------------------------------: |
| <img src="../../assets/images/data_store/viewDataset3.png" alt="drawing" width="600"/>      |

## Metadata fields
The metadata page has the following information

- **Metadata**
    - Handle 
    - Dataset location
      - Bucket
      - Path
      - URI
    - Record Information
      - Created time
      - Updated time
- **Dataset Information**
  - Date created
  - Dataset name
  - Dataset description
- **Author information**
    - Author name
    - Author email
    - Author ORCID
- **Author Organisation Information**
    - Name
    - ROR
- **Publisher Information**
    - Publisher name
    - Publisher ROR  
- **License**
   - URL
- **Keywords**   
- **JSON Metadata**

## Collaborating
Users can share the dataset with others using the Handle link. Using the Handle link to share data is an easy way of sharing files as updates to the data can be made and the user with the link will always have access the most up to date data.
The Handle link is a persitent digital identifier for the dataset. See [About digital object identifiers](../digital-object-identifiers.html){:target="\_blank"} for more information.  
  
To share, click on the **Click to copy link** button. Then paste the link into an email, document etc... that is to be shared with other RRAP M&DS IS users. 

|                                     Share dataset                           |
| :-------------------------------------------------------------------------: |
|<img src="../../assets/images/shareDataset.png" alt="drawing" width="200" align ="left"/>      | 
 

{% include notes.html content=" Users <strong>must</strong> to be logged into the RRAP M&DS Information System to be able to access the data. Users without an Information System account will need to create one before viewing the data." %}

Underneath the Handle link, the **Dataset Location** information relates to the storage location on the AWS S3 server. The **Record Information** gives the user the date and time of the creation of the metadata record, with any updates to the metadata record shown under *Updated time*.

On the right hand side of the page, Users have an overview of the the metadata and can also [download the dataset](../data-store/downloading-datasets.html){:target="\_blank"} and [upload additional data](../data-store/registering-and-uploading-a-dataset.html){:target="\_blank"} by clicking the corresponding tabs. The **JSON Metadata** can be expanded (so the information can be viewed or copied) by clicking on the **Expand details** button. To close, click the **Expand details** button again. 

