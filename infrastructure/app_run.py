#!/usr/bin/env python3
import typer
from configs.config_map import get_app_config, get_ui_only_config, all_app_configs
from enum import Enum
from typing import List
import os


"""
This is a Typer CLI Python script which dispatches CDK commands with an
appropriate --app, --output and stack name based on the deployment config ID. 

The config ID is looked up against the config map imported above. Within this
config is the cdk app name and output path used to determine the appropriate cdk
command.

All arguments after the defined set below are appended to the end of the CDK
command.
"""

# Define the available set of IDs as a nice string
app_config_id_helper = f"[{', '.join(all_app_configs)}]"


# The provena app defines a pipeline and app target. Pipeline = the pipeline stack, App = The app stack
class RunTarget(str, Enum):
    APP = "app"
    PIPELINE = "pipeline"

app = typer.Typer()


@app.command()
def run(
    config_id: str = typer.Argument(
        ...,
        help=f"What config ID do you want to run this CDK command against? Available: {app_config_id_helper}.",
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
        app_config_generator = get_app_config(config_id)

        if app_config_generator is None:
            print(
                f"The specified config ID was not a valid target: {config_id = }. Aborting.")
            typer.Exit(code=1)

        assert app_config_generator

        app_config = app_config_generator()
        assert app_config

        print("App config determined and validated.")
        pipeline_stack_id = app_config.deployment.pipeline_stack_id
        deployment_stack_id = app_config.deployment.deployment_stack_id
        input_output_subcommand = app_config.deployment.cdk_input_output_subcommand

    else:
        ui_config_generator = get_ui_only_config(
            config_id)

        if ui_config_generator is None:
            print(
                f"The specified config ID was not a valid target: {config_id = }. Aborting.")
            typer.Exit(code=1)

        assert ui_config_generator

        ui_config = ui_config_generator()

        assert ui_config

        print("UI config determined and validated.")
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
