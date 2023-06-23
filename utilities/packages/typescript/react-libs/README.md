# React shared libraries Provena

Set of shared functionality which is reused between multiple UI components.

## Usage

Each of the consuming UI libraries are setup to perform a build linking step which embeds a symlink into this folder.

This was required due to a Vite build time bug which broke context provider functionality.


Importing from the lib uses a single global scope e.g.

```typescript
import { ComponentName, useSomeHook } from "react-libs";
```

## Contents

### Components

Contains react components with various functions. Notably contains the form overrides used in the RJSF forms in Registry and Data Store. Also notably contains the Json detail renderered used in nearly all UIs now.

### Hooks

Contains various custom hooks which are consumed by the Components or used on their own. Require the queries + auth from the keycloak setup.

### Interfaces

Contains some helpful interfaces/types and helper funcs on those e.g. the hookInterfaces.

### Layout

Contains some layout helper components such as ProtectedRoute.

### Queries

Uses the API endpoints to perform typed queries. Returns Promise objects for the response type. Used extensively in the custom hooks.

### Stores

Some classes/stateful stores - notably contains the keycloak and api agent stores which interact with each other to provide authorised API requests.

### Tasks

Currently just contains the Lambda warmer background task.

### Util

Various utility/helper functions.

## Requirements

### Env variables (required at build/run time)

If you don't have these at runtime the shared lib throws an error.

**API Endpoints:** (mandatory)

-   VITE_AUTH_API_ENDPOINT
-   VITE_REGISTRY_API_ENDPOINT
-   VITE_SEARCH_API_ENDPOINT
-   VITE_WARMER_API_ENDPOINT

**Keycloak Auth Links and Config:** (mandatory)

-   VITE_KEYCLOAK_CLIENT_ID
-   VITE_KEYCLOAK_AUTH_ENDPOINT

**UI Links:** (recommended - dead links if not provided)

-   VITE_LANDING_PAGE_LINK
-   VITE_DATA_STORE_LINK
-   VITE_PROV_LINK
-   VITE_REGISTRY_LINK
