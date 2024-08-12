## Quick Start

Create a local .env file. Add a github token with API repo access to the target repo

i.e.

```
GITHUB_TOKEN="1234"
```

Setup and install python venv

```
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run CLI and explore tooling

```
python manager.py --help
```

To delete stale deployments

```
python manager.py delete-stale
```

To force without warnings

```
python manager.py delete-stale --force
```

## Prerequisites

-   Token: need to have a GITHUB_TOKEN env variable with a github API token which has repo access to target repo
-   AWS creds: need to have an active AWS CLI session with permission to Cloudformation actions in the account - i.e. DescribeStacks, ListStacks, DeleteStack
