---
layout: default
title: Admin-only deletion
nav_order: 8
parent: Admin tools
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

# Admin-only deletion

This page documents how to delete items as an admin-only function. Deleting using the admin tools described below is considered a last resort operation. 

You will need to have an activated user account on Provena with the admin role assigned as a pre-requisite to deleting items as an admin-only function.

## What can be deleted?

Currently these types can be deleted:
* Model Run
* Study

Some constraints around what can be deleted:
* Items can only be deleted if it is not connected to anything else (i.e. no dependencies)
* Only the latest version of an item can be deleted (otherwise, the versioning system's integrity is broken)

## How to delete items?

Scripts for managing a Provena deployment including deletion operations are available here:
https://github.com/provena/scripts/tree/main

See https://github.com/provena/scripts/tree/main/scripts#permanently-deleting-files for documentation on deletion commands.