# API Authentication Helper Scripts

## How to run these scripts

### Pre-requisites

- Valid python installation - version >=3.8
- Internet connection
- Provena deployment

### Setup

#### Create a python virtual environment

Linux:

```bash
python -m venv .venv
```

Windows

```
python -m venv c:/path/to/env
```

#### Source venv

Linux:

```bash
source .venv/bin/activate
```

Windows (cmd.exe)

```
<venv path>\bin\activate.bat
```

Windows (powershell)

```
<venv path>\bin\activate.ps1
```

#### Install dependencies

On all systems:

```bash
pip install -r requirements.txt
```

### Running a script

These scripts use the [Typer CLI](https://typer.tiangolo.com/typer-cli/) tool which generates easy to use CLIs with built in help functions.

To learn about a script, use the `--help` option e.g.

```
python offline_tokens.py --help
```

## Setting up your Provena environment

Before running the script, you will need to setup the file `../environments.json` with the appropriate target deployment. See `../README.md` for instructions on how to do this.

## Offline Token Management

The `offline_tokens.py` script provides some actions which help generate and test offline tokens.

### Generate a new offline token

To generate an offline token you can use the `generate-offline-token` action of the `offline_tokens.py` script, like so:

```
python offline_tokens.py generate-offline-token <STAGE> <output file path>
```

Ensure the STAGE used matches the previously setup environment in the `../environments.json` file.

You should only do this process once, then **securely store the token and delete the file**.

For example, to generate a production offline token to the file `token.txt` you could use the following command.

```
python offline_tokens.py generate-offline-token PROD token.txt
```

As part of this process, a browser tab should open where you will need to login to your account and provide consent for this request.

**Make sure that you move your token to secure storage such as a secret manager and delete this file! This token provides indiscriminate access to your system permissions.**

### Test the offline token

To test an existing offline token you can use the `test-offline-token` action of the `offline_tokens.py` script, like so:

```
python offline_tokens.py test-offline-token <STAGE>
```

Before running this script, you need to export the offline token as an environment variable called `PROVENA_OFFLINE_TOKEN`.

On linux/bash, for example:

```
export PROVENA_OFFLINE_TOKEN=$(cat token_file.txt)
```

On windows CMD, for example:

```
set /P PROVENA_OFFLINE_TOKEN=< <file_name>
```

If you receive an exception indicating that your token was not present, double check that the environment variable was correctly exported.

If you receive an exception from the authorisation, it is likely that your token is not valid, or that it is for the wrong stage.
