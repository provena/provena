---
layout: default
title: Device Auth Flow
nav_order: 2
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

# Device Auth Flow

## Overview

The [OAuth device auth flow](https://www.oauth.com/oauth2-servers/device-flow/) is easy to use and is suitable for minimal or even no input environments (such as automated scripts).

However, this process requires **intermittent user interaction** to approve the authorisation using a browser on an internet connected device with a Web Browser.

## Process Summary

The OAuth device auth flow is completed through a series of steps. For more detailed information, see the [OAuth device auth flow documentation](https://www.oauth.com/oauth2-servers/device-flow/). The steps are summarised below:

-   the device (e.g. script/computer) makes a request to initiate a device authentication flow to our authentication server
-   the authentication server responds with a URL which includes a device code and other metadata which the device stores
-   the device polls the authorisation server at a specific endpoint at the specified polling interval, awaiting the user's confirmation, meanwhile,
-   the user opens the link on that device, or another device, logs in to the authentication server using the browser, and confirms access
-   the device receives a successful response from the authentication server which includes an **access token** and **refresh token**

## Implementation Details

When integrating the device auth flow into your workflows, the following should be ensured:

-   the correct authorisation server is being used
-   the correct token and device endpoints are being used
-   the refresh and access tokens are stored so that the device can perform an automatic refresh without user input up to the maximum life of the session (around 8 hours)
-   the access and refresh tokens are not leaked into logs or other unprotected outputs

## Implementation Examples

### Python

The [Provena Client Tools](https://github.com/gbrrestoration/mds-is-client-tools) Python library implements a complete Device Auth Flow example.

The source code for the tool is available [here](https://github.com/gbrrestoration/mds-is-client-tools/blob/main/src/mdsisclienttools/auth/TokenManager.py).

Some implementation notes:

-   the `DeviceFlowManager` expects a `keycloak_endpoint` as an input argument - use `https://auth.mds.gbrrestoration.org/auth/realms/rrap`.
-   by default, the access and refresh tokens are cached in a local file called `.tokens.json` - this avoids having to repeatedly login
-   the class `DeviceFlowManager` exposes a method `get_auth` which can be used directly with the Python `Requests` library - an example of using this method is provided as discussed below
-   a browser window is automatically opened when possible - otherwise, the user would need to open the link themselves

The blog [notebooks](https://gbrrestoration.github.io/rrap-demo-blog/) make extensive use of this authorisation workflow and serve as a good example of how to use it.
