# Prov admin tools

## Neo4j restorer

The prov API has some admin endpoints which enable re-lodging of existing provenance records into the graph store. This could be helpful to restore the graph store to a healthy state after data loss or corruption.

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
python neo4j_restorer.py --help
```

To explore options for a command, see

```
python neo4j_restorer.py <command name here> --help
```

e.g.

```
python neo4j_restorer.py restore-all-model-runs --help
```

### Restoring a single model run

If you know the handle of the model run, then use:

```
python neo4j_restorer.py restore-model-run-from-handle <handle id> <stage>
```

If you have a file which contains the model run as a json payload (e.g. after fetching from the registry), you can restore directly from a completed model run record in a file:

```
python neo4j_restorer.py restore-model-run-from-file <file name e.g. input.json> <stage>
```

### Restoring all items

If you want to restore all **complete** model run records in the registry, then you can use

```
python neo4j_restorer.py restore-all-model-runs <stage>
```

There are a lot of extra options to this method, see:

```
python neo4j_restorer.py restore-all-model-runs --help
```

for the details. Notably, to avoid re-lodging the same records repeatedly, you should make use of the --completed-items option to skip already processed items upon repeated runs of the script. This file is auto generated upon completion, or you can manually populate it yourself with records you want to skip/have already processed.

### Overriding endpoints

All of the functions have options to override the API endpoints using either `--registry-endpoint-override` or `--prov-endpoint-override` for the registry API and prov API respectively. This could be helpful if you are running a customised API locally which you want to run/test against. The default mappings from stage names to API are configured in `config.py`.

## Graph admin 

The graph admin tool currently holds only a prov-api API wrapper for the clear graph operation.

WARNING - this operation will delete all nodes from the active neo4j graph backing the prov API at either the default or specified endpoint. 

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
python graph_admin.py --help
```

To run a clear 

```
python graph_admin.py TEST
``` 

then dismiss the warnings. 

To force headless operation (dismissing warnings) use 

```
python graph_admin.py TEST --force
``` 

and to override the endpoint use:

```
python graph_admin.py TEST --prov-endpoint-override http://localhost:8000
``` 

where you can use whatever endpoint is hosting the prov API you want to target.
