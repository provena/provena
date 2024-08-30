# GitHub Credentials Bootstrap CDK Stack

## Purpose

This CDK stack is very simple, it just deploys a GitHub connection credential which CodeBuild can use to authenticate with GitHub.

This is a dependency for the main CDK pipeline workflow, but is managed in a separate project to keep the main CDK app simple.

## Config management

This project shares a configuration management approach from the main CDK infrastructure application.

For more detailed explanation of the configuration setup, see [README](../../../README.md).

To get setup

```bash
# Return to root of Provena repo - depends on your installation
cd ../path/provena

# run the config script to pull config for your desired stage
# if used previously, you won't need to specify the config repo string
./config namespace stage [--target repo-clone-string]
```

This will pull down your config repo's configs for the GitHub bootstrap.

### Config schema

The config schema is documented in `config.py`. This includes comments explaining the variables.

`sample.json` is provided as a starting point. Make sure not to use sample as the name of your config as this will be committed to version control.

## Python setup

Create venv, source and install.

```
python3.10 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
```

## How to deploy/update

### AWS Creds

Ensure for your target deployment you have the appropriate AWS creds setup.

### Determine config target

Config files are named `<config id>.json` where config ID is always lower cased in the file system.

For example, if you have a config called `dev.json` then specify this using an environment variable or preceding variable e.g.

```
export CONFIG_ID=dev
```

or

```
CONFIG_ID=dev cdk ...
```

### Diff

Replacing `dev` with your preferred target.

Run

```
CONFIG_ID=dev cdk diff
```

Check the diff to ensure your changes are desirable.

### Deploy

Run

```
CONFIG_ID=dev cdk deploy
```

Check the diff to ensure your changes are desirable.
