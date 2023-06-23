# Environment Bootstrapper

This tool sets up all of the APIs with a comprehensive .env file as per the
currently deployed API. This tool can be targetted for each admin tooling
environment. By default it will overwrite .env, but you can specify instead that
a new file name is created.

This CLI tool is built using [Typer](https://typer.tiangolo.com/). It produces a
helpful CLI interface including sub commands, help functions, and auto
completion.

## Quickstart

Ensure you are working in this directory in your terminal. Use the recent python
executable which is visible for your system, in my case it is `python3.10`.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You can run the environment bootstrapper script using typer e.g.

```
python environment_bootstrapper.py --help
```

To bootstrap a given tooling environment, use

```
python environment_bootstrapper.py <env name>
```

This will pop open a browser window to log you in if you have no cached
credentials.

## Command documentation

See the quickstart above to setup your python virtual environment.

The `environment_bootstrapper.py` script is self documenting. Use the `--help`
option to see a list of commands, then include the command and `--help` to see
the options for that command. E.g. `python environment_bootstrapper.py
bootstrap-stage --help`.

### Bootstrapping a stage

To setup config files for all apis of a tooling environment, use:

```
python environment_bootstrapper.py bootstrap-stage <tooling environment name>
```

**Note**: To understand more about the tooling environments, see the parent folder's
README and the directory in the parent folder named "tooling-environment-manager". 

To see options to customise behaviour and allowed values, use:

```
python environment_bootstrapper.py bootstrap-stage --help
```

### Bootstrapping a single API

To retrieve a config file for one api of a stage, use:

```
python environment_bootstrapper.py fetch-api-config <tooling environment name> <api name>
```

where the api name is one of
`auth-api|data-store-api|prov-api|registry-api|search-api|identity-api`. To
write the output to a
file, use the `--output-file` option. To see options to customise behaviour and
allowed values, use:

```
python environment_bootstrapper.py fetch-api-config --help
```

### Bootstrapping a feature branch (Advanced)

If you are implementing a feature branch deployment workflow (discussed in the
admin-tooling readme) you can also use this tool to deliver environment files
for the feature deployments.

We use the --param option to pass in the feature number. This requires a feature
environment to be defined in the admin-tooling/environments.json file.

```
python environment_bootstrapper.py bootstrap-stage feature --suppress-warnings --param feature_number:${ticket_no}
```

where `ticket_no` is passed from the environment, or, you may directly provide the
ticket number in the command.
