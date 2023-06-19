---
layout: default
title: Digital object identifiers
nav_order: 6
---
# About digital object identifiers
<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
- TOC
{:toc}
____
</details>

## What digital object identifier infrastructure is Provena IS using? 
Provena IS is using Australian Research Data Commons (ARDC) [Handle Service](https://ardc.edu.au/services/identifier/handle/){:target="\_blank"} for creating persistent references to digital research objects.

___
### Handle.net 
Handle.net is a service which maintains a registry of digital identifiers that are used to persistently identify digital objects.  It also provides a service to resolve the location of previously minted objects.

___
### Minting
Minting a digital identifier is the process of requesting a unique number from a Handle Service and associating it with a Uniform Resource Locator (URL), a unique sequence of characters that identifies a logical or physical resource used by web technologies.

As part of using the **Data Store** functionality to registry a dataset and the **Registry** to register an entity, a Handle Identifier is minted and will be associated with the metadata for the dataset or entity, respectively. 

___
### What can I do with a Handle identifier?
The identifier can be used to persistently find a digital resource. Over time, a URL to the resource may change as digital assets are relocated. In this scenario, the Handle record, which is made up of the identifier and the URL, can be maintained by updating the URL reference in the Handle record to point to the new location without having to change the Handle identifier.  