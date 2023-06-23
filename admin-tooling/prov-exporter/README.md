# Prov exporter

The script uses Typer and is mostly self documenting. Basic usage is described below.

### Quick start

Setup your python venv

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you need dev dependencies (formatting, typing etc), also run

```
pip install -r dev-requirements.txt
```

Once you have your venv setup and sourced you can see the script help with

```
python prov_exporter.py --help
```

To explore options for a command, see

```
python prov_exporter.py <command name here> --help
```

e.g.

```
python prov-exporter.py generate-export-local --help
```

### Running an export

Use the generate-export-local command:

```
Usage: prov-exporter.py generate-export-local [OPTIONS] REPORT_TYPE:{MODEL_RUN
                                               _LISTING|DETAILED_LISTING}
                                               OUTPUT_PATH
                                               STAGE:{TEST|DEV|STAGE|PROD}

 Given a handle ID, will pull the model run record from the stage's registry, and run a restore into the neo4j graph db using the prov API admin endpoint. Requires registry READ and prov store ADMIN
 permissions.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    report_type      REPORT_TYPE:{MODEL_RUN_LISTING|DETAILED_LISTING}  The report type to generate. [default: None] [required]                                                                              │
│ *    output_path      FILENAME                                          The filename to write the CSV to. [default: None] [required]                                                                         │
│ *    stage            STAGE:{TEST|DEV|STAGE|PROD}                       The Stage in which this record exists and will be restored into. One of: "DEV" "TEST" "STAGE" "PROD". [default: None] [required]     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --token-refresh                 --no-token-refresh          Force a token refresh, invalidating cached tokens. Can be used if you have updated your token permissions and don't want to use an out-dated     │
│                                                             access token.                                                                                                                                    │
│                                                             [default: no-token-refresh]                                                                                                                      │
│ --registry-endpoint-override                          TEXT  The URL of the registry API endpoint to use. By default the live endpoint for the given stage is used. [default: None]                           │
│ --timezone                                            TEXT  The timezone to use formatted as Country/City. I.e. [Australia/Adelaide, Australia/Brisbane, Australia/Broken_Hill, Australia/Darwin,            │
│                                                             Australia/Eucla, Australia/Hobart, Australia/Lindeman, Australia/Lord_Howe, Australia/Melbourne, Australia/Perth, Australia/Sydney].             │
│                                                             [default: Australia/Sydney]                                                                                                                      │
│ --help                                                      Show this message and exit.                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

e.g.

```
python prov-exporter.py generate-export-local MODEL_RUN_LISTING exports/test.csv DEV --timezone "Australia/Perth"
```
