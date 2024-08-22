import typer
import json
import os
from helpers.github_helpers import *
from helpers.aws_helpers import *
from helpers.misc_helpers import *
from typing import List, cast
from rich import print
from config import config

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def list_stale(
    verbose: bool = typer.Option(
        False,
        help="Shows the verbose output which includes all info about each stale feature deployment."
    )
) -> None:
    """
    list_stale 

    Lists all feature branches found which have MERGED PRs yet still have
    deployed (non deleted) stacks.

    """
    status_info_dict = get_status_infos()
    stale = list(filter(is_stale, status_info_dict.values()))
    if len(stale) == 0:
        print(f"No stale feature deployments found!")
    else:
        print(f"Stale feature deployments:")
        for s in stale:
            if verbose:
                print(s)
            else:
                print(s.ticket_num)


@app.command()
def delete_stale(
    force: bool = typer.Option(
        False, help=f"Force yes - no prompts. Use in headless.")
) -> None:
    status_info_dict = get_status_infos()
    stale = list(filter(is_stale, status_info_dict.values()))

    if len(stale) == 0:
        print(f"No stale feature deployments found!")
        exit(0)

    all_stacks: List[Dict[str, Any]] = []
    for s in stale:
        if s.pipeline_stack:
            all_stacks.append(s.pipeline_stack.stack_data)
        if s.app_stack:
            all_stacks.append(s.app_stack.stack_data)

    if not force:
        response = yes_or_no(
            f"There are {len(all_stacks)} stacks to delete, proceed?")
        if not response:
            print("Aborting...")
            exit(1)
    manage_deletion_lifecycle(stacks=all_stacks, force=force)


@app.command()
def delete_listed(
    feature_ids: List[str],
    force: bool = typer.Option(
        False, help=f"Force yes - no prompts. Use in headless.")
) -> None:

    # manually create stack info sufficient for deletion
    names: List[str] = []

    for id in feature_ids:
        pipeline_stack = config.build_pipeline_stack_name(id)
        deploy_stack = config.build_app_stack_name(id)
        names.append(pipeline_stack)
        names.append(deploy_stack)

    stacks = get_stacks_by_name(names=names)

    if not force:
        response = yes_or_no(
            f"There are {len(stacks)} stacks to delete, proceed?")
        if not response:
            print("Aborting...")
            exit(1)
    manage_deletion_lifecycle(stacks=stacks, force=force)


@app.command()
def check_status_by_id(
    ticket_num: int = typer.Argument(
        ...,
        help="The JIRA ticket number for the feature branch"
    )
) -> None:
    status_info_dict = get_status_infos()

    # try and find the ID
    status = status_info_dict.get(ticket_num)

    if status:
        print(status)
        print(
            f"This deployment {'IS' if is_stale(status) else 'IS NOT'} stale")
    else:
        print("Could not find any stacks and/or PRs which reference this ticket number!")


if __name__ == "__main__":
    app()
