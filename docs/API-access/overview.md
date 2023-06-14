---
layout: default
title: Overview
nav_order: 1
grand_parent: Information System
parent: API Access
---

{: .no_toc }

<details  open markdown="block">
  <summary>
    Table of contents
  </summary>
{: .text-delta }
* TOC
{:toc}
____
</details>

# API Access Overview

All RRAP IS services can be accessed by authorised users through the system APIs.

These APIs can be integrated in an automated way into any internet connected computing environment.

All RRAP user interfaces use these APIs to perform system operations - anything that can be done through the interfaces can be automated using the RRAP IS APIs.

## Endpoints and documentation

The RRAP IS APIs are [REST](https://www.redhat.com/en/topics/api/what-is-a-rest-api)ful Python [ASGI](https://asgi.readthedocs.io/en/latest/) compliant services. The API endpoints are linked below. Each API publishes two documentation pages:

-   **Data Store API**:
    -   API: [https://data-api.mds.gbrrestoration.org](https://data-api.mds.gbrrestoration.org)
    -   Swagger Documentation: [https://data-api.mds.gbrrestoration.org/docs](https://data-api.mds.gbrrestoration.org/docs)
    -   Redoc Documentation: [https://data-api.mds.gbrrestoration.org/redoc](https://data-api.mds.gbrrestoration.org/redoc)
-   **Registry API**:
    -   API: [https://registry-api.mds.gbrrestoration.org](https://registry-api.mds.gbrrestoration.org)
    -   Swagger Documentation: [https://registry-api.mds.gbrrestoration.org/docs](https://registry-api.mds.gbrrestoration.org/docs)
    -   Redoc Documentation: [https://registry-api.mds.gbrrestoration.org/redoc](https://registry-api.mds.gbrrestoration.org/redoc)
-   **Provenance API**:
    -   API: [https://prov-api.mds.gbrrestoration.org](https://prov-api.mds.gbrrestoration.org)
    -   Swagger Documentation: [https://prov-api.mds.gbrrestoration.org/docs](https://prov-api.mds.gbrrestoration.org/docs)
    -   Redoc Documentation: [https://prov-api.mds.gbrrestoration.org/redoc](https://prov-api.mds.gbrrestoration.org/redoc)
-   **Auth API**:
    -   API: [https://auth-api.mds.gbrrestoration.org](https://auth-api.mds.gbrrestoration.org)
    -   Swagger Documentation: [https://auth-api.mds.gbrrestoration.org/docs](https://auth-api.mds.gbrrestoration.org/docs)
    -   Redoc Documentation: [https://auth-api.mds.gbrrestoration.org/redoc](https://auth-api.mds.gbrrestoration.org/redoc)

## How to use the RRAP APIs

There are some pre-requisites to using the RRAP IS system APIs:

-   You need to be an authorised user - see [logging in](../getting-started-is/logging-in) and [requesting access](../getting-started-is/requesting-access-is).
-   You need to be in a programmatic environment where you can make HTTPS REST API calls - we use Python for all of our examples though the implementation in other programming or scripting languages would be very similar
-   You need to establish an API authentication workflow - see [API Authentication](./authentication) for detailed instructions
