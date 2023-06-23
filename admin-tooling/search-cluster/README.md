# Search Cluster Helpers - WIP

A set of CLI tools which help smooth out interactions with the AWS open search
cluster deployed on each stage which runs the registry and data store search
service.

## Quick start

### Setup venv

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run a command

The `reindex.py` and `run_command.py` scripts use typer CLI which is part of the virtual environment setup. You can learn about the methods and their arguments by using the format

```
python <script.py> --help
```

For example

```
python reindex.py --help
```

which gives

```
 Usage: reindex.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                                                                 │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                                          │
│ --help                        Show this message and exit.                                                                                                                                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ reindex-data-store                                                                                                                                                                                      │
│ reindex-registry                                                                                                                                                                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Reindex

## Authentication
