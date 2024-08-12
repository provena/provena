#!/usr/bin/env python3
import typer
from provena.config.config_loader import get_app_config, get_ui_only_config
from enum import Enum
from typing import List
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
    ui_only: bool = typer.Option(
        False,
        help=f"Do you want to deploy/modify a UI only stack?"
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

    # standard deployment
    if not ui_only:
        # get the app config
        try:
            app_config_loader = get_app_config(config_id)
            app_config = app_config_loader()
        except Exception as e:
            raise Exception(f"Failed to load config with config ID {config_id}. Error.") from e

        print("App config loaded and validated. Success.")

        pipeline_stack_id = app_config.deployment.pipeline_stack_id
        deployment_stack_id = app_config.deployment.deployment_stack_id
        input_output_subcommand = app_config.deployment.cdk_input_output_subcommand

    else:
        # get the app config
        try:
            ui_config_loader = get_ui_only_config(config_id)
            ui_config = ui_config_loader()
        except Exception as e:
            raise Exception(f"Failed to load ui only config with config ID {config_id}. Error.") from e

        print("UI only app config loaded and validated. Success.")
        pipeline_stack_id = ui_config.pipeline_stack_id
        deployment_stack_id = ui_config.deployment_stack_id
        input_output_subcommand = ui_config.cdk_input_output_subcommand

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
