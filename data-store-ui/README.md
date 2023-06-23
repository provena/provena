# Provena Data Store UI

The Provena Data Store UI is a Typescript React GUI which enables user friendly interaction with the Provena Data Store.

This UI enables:

-   dataset registration
-   dataset searching
-   dataset metadata updates
-   dataset download
-   dataset upload

and more...

We recommend deploying all the Provena UIs using the CDK deployment system in the `infrastructure/cdk-infrastructure` folder of this repository.

However, advanced users can follow the steps below to deploy a local development instance of this GUI which can interface with a configurable set of Provena APIs.

## Setup

### Installation

We recommend using [node version manager](https://github.com/nvm-sh/nvm) (nvm) to manage your installed Node instance.

Once you have `nvm` installed, install node 16 using `nvm`:

```
nvm install 16
```

and activate it:

```
nvm use 16
```

Now ensure you are working in this folder, and install the dependencies.

```
npm i
```

### Environment variables

The UI cannot run or function properly without a set of required environment variables. To help manage these variables, `.env` files are used.

The `package.json` scripts section defines an example build and start target: `build:example` and `start:example`. These scripts use the `.env.example` file to load environment variables.

We do not recommend running the UI unless you have a deployed Provena instance.

To setup the UI to target your deployed Provena application, copy the example build scripts into two new scripts, for a deployment of your preferred name e.g. `provena` i.e.

```
    // package.json
    ...
    "scripts": {
        ...
        "build:example": "npx tsc && env-cmd -f .env.example vite build",
        "start:example": "npx tsc && env-cmd -f .env.example vite",

        "build:provena": "npx tsc && env-cmd -f .env.provena vite build",
        "start:provena": "npx tsc && env-cmd -f .env.provena vite",
    }
    ...
```

Note that we also change the name `.env.example` to `.env.provena`.

Now make a copy of the `.env.example` file named `.env.provena`. This will form the basis for you to modify your environment to suit your customised Provena deployment.

You will notice in this file there are a few variables you should replace.

-   YOUR_BASE_DOMAIN = The deployed application url without any protocol e.g. `your.domain.com`
-   YOUR_KEYCLOAK_REALM_NAME = The deployed keycloak realm name
-   YOUR_CONTACT_US_LINK = The URL that will be opened when the contact us button is pressed

You could also update the documentation URL if desired - it defaults to the provena docs.

Once you have completed the env file, you should have a functional set of environment variables.

## Run

To run the server locally (replacing provena with your chosen deployment target name as above)

```
npm run start:provena
```

To build the application locally:

```
npm run build:provena
```

## Developer Notes

### Authorisation

Depending on the application stage of your deployed Provena application, the CORS settings may be unsuitable for running a local server. The local server will only work on a DEV stage deployment (since it has non restrictive CORS policies). There isn't an easy workaround for this, you could:

-   redeploy your application to a different stage
-   manually update the CORS settings of your deployed application
-   run the browser in a compromised security mode which doesn't enforce CORS preflight checks

### Build system

[Vite](https://vitejs.dev/) is used to build and serve the application. We migrated from create react apps to Vite to enable hot module reloading, faster building and better minimisation.

### React Libs

Due to an issue in the Vite build process (which we haven't fully isolated), relative package installs caused context provider errors (for example, the MUI theme).

A suitable workaround in our context was to symlink the react-libs library as a preinstall step.

You will notice a symlink to the react libs shared library in this repo, within the `src/react-libs` folder. This allows you to import like normal `import {...} from 'react-libs';` and also edit the package contents in a consistent way between the various UIs.
