#!/usr/bin/env python3
import typer
from provena.config.config_loader import get_config
from provena.config.config_class import DeploymentType, ProvenaConfig, ProvenaUIOnlyConfig
from enum import Enum
from typing import List, cast
import os


"""
This is a Typer CLI Python script which dispatches CDK commands with an
appropriate --app, --output and stack name based on the deployment config ID. 

The config ID must correspond to a config file in configs/ of the same name + .json.

All arguments after the defined set below are appended to the end of the CDK
command.
"""

# The provena app defines a pipeline and app target. Pipeline = the pipeline stack, App = The app stack
class RunTarget(str, Enum):
    APP = "app"
    PIPELINE = "pipeline"

app = typer.Typer()


@app.command()
def run(
    config_id: str = typer.Argument(
        ...,
        help=f"What config ID do you want to run this CDK command against?",
    ),
    run_target: RunTarget = typer.Argument(
        ...,
        help=f"What app target do you want to use. app or pipeline."
    ),
    commands: List[str] = typer.Argument(
        ...,
        help=f"What CDK commands do you want to run - all postfixed onto the end of the cdk ... command."
    )

) -> None:
    # determine stack IDs
    pipeline_stack_id: str = ""
    deployment_stack_id: str = ""
    input_output_subcommand: str = ""

    # load config
    app_config_loader = get_config(config_id)
    config = app_config_loader()

    # standard deployment
    if config.type == DeploymentType.FULL_APP:
        print("FULL_APP App config loaded and validated. Success.")

        # cast
        config = cast(ProvenaConfig, config)

        # determine stack IDs and command
        pipeline_stack_id = config.deployment.pipeline_stack_id
        deployment_stack_id = config.deployment.deployment_stack_id
        input_output_subcommand = config.deployment.cdk_input_output_subcommand
    elif config.type == DeploymentType.UI_ONLY:
        print("UI_ONLY App config loaded and validated. Success.")

        # cast
        config = cast(ProvenaUIOnlyConfig, config)

        # determine stack IDs and command
        print("UI only app config loaded and validated. Success.")
        pipeline_stack_id = config.pipeline_stack_id
        deployment_stack_id = config.deployment_stack_id
        input_output_subcommand = config.cdk_input_output_subcommand
    else: 
        raise ValueError(f"Unexpected DeploymentType in base config: {config.type}. Report to system administrator.")
    # build command string

    # work out target stack name
    stack_name: str = ""
    if run_target == RunTarget.APP:
        stack_name = f"{pipeline_stack_id}/deploy/{deployment_stack_id}"
    elif run_target == RunTarget.PIPELINE:
        stack_name = f"{pipeline_stack_id}"

    # variable io part e.g. --app "" --output ""
    actions = " ".join(commands)
    command = f"cdk {input_output_subcommand} {actions} {stack_name}"

    print(f"Exporting provena config ID to assist in running stack.")
    os.environ['PROVENA_CONFIG_ID'] = config_id

    print(f"Running command '{command}'")
    os.system(command)


if __name__ == "__main__":
    app()
