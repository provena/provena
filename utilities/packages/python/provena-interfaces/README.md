# Provena-Interfaces

Provena-Interfaces is a Python package that provides interfaces for the Provena Application. It includes a set of interfaces that are used to interact with the Provena system. The interfaces are especially useful for parsing response payloads from the API, and for creating requests to the API. The interfaces will sit adjacent to (and be consumed by) a ProvenaClient library which is a work in progress.

## Installation

Services defined in this repo build/install directly from this directory. Developing outside of the repo, you can install the package using pip:

```bash
pip install provena-interfaces
```

## Building and Publishing
The package is built and published using a GitHub Actions workflow defined in this repo's .github/worklows. The workflow is triggered on releases and will publish the publish with the same version as the rest of the Provena application. This means the Provena app and ProvenaInterfaces will have the same version numbers.

## Package REAMDE
When updating this README, please also update the **package-readme.py** file in this directory appropriately. It should contain information releveant to the package only (not build and publish logic). It will be displayed on the package's PyPi page.
