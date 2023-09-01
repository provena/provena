---
layout: default
title: Overview
nav_order: 1
grand_parent: API Access
parent: API Authentication
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

# API Authentication

Access to any Provena API requires providing proof of your system access. System access is controlled through a set of roles for each of the services.

Authentication is provisioned by a authentication server and signed using the [JSON Web Token](https://jwt.io/introduction) (JWT) standard.

Sending signed JWTs over an encrypted HTTPS connection is a trusted and secure way to communicate your authorisation.

There is currently one supported method of script-ready authentication:

-   [OAuth device auth flow](https://www.oauth.com/oauth2-servers/device-flow/) - this authentication flow is easy to use and is suitable for minimal or even no input environments (such as automated scripts). However, this process requires **intermittent user interaction** to approve the authorisation using a browser on an internet connected device. For more information about using the device auth flow, see [here](./device-auth-flow).

We are also in the process of designing and documenting an API authorisation pattern which will enable completely automated, headless API operations without user interaction.

You can make an authenticated API call by including an `Authorization` Header with the value `Bearer <your access token here>`. Each of the APIs expose a set of access check endpoints which enable you to check your access to the API in a predictable way e.g. [data store check-write-access](https://data-api.mds.gbrrestoration.org/docs#/Access%20check/check_write_access).

Authorisation is established by decoding the JWT, verifying the signing signature, and reading the list of roles that your user has been granted. You can check what roles you have access to and request additional access by [logging in](../../../getting-started-is/logging-in) and visiting the [roles view of your profile](../../../getting-started-is/requesting-access-is).
