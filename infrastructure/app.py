#!/usr/bin/env python3
import aws_cdk as cdk
import os
from provena.pipeline.pipeline_stack import ProvenaPipelineStack, ProvenaUIOnlyPipelineStack
from provena.config.config_helpers import validate_config
from provena.config.config_loader import get_config
from provena.config.config_class import DeploymentType, ProvenaConfig, ProvenaUIOnlyConfig
from typing import cast

"""
This manages a provena app deployment. The config is dispatched based on the
config ID. This config ID must be present in the imported config map from
configs.config_map. This allows organisational extension of private
configurations while retaining a fully typed config interface.

Capable of referring to the base type field in the config and dispatching to
correct stack (app or UI only).
"""

# Dispatch from config ID
# =========================

config_id = os.getenv("PROVENA_CONFIG_ID")

if config_id is None:
    raise ValueError("No PROVENA_CONFIG_ID environment variable provided.")

config_loader = get_config(config_id)
config = config_loader()

# Determine type 
if config.type == DeploymentType.FULL_APP:
    print(f"Identified app type: {config.type}.")

    # Validate imported config
    # =========================

    config = cast(ProvenaConfig, config)

    # Validate config
    validate_config(config)

    print(
        f"Config ID identified and validated successfully - running against {config_id = }.")

    # This app is for the ops deployment of STAGE
    app = cdk.App()

    """
    =========================
    DEPLOYMENT PIPELINE STACK
    =========================
    This should be the only stack in the deployment pipeline.
    """

    ProvenaPipelineStack(
        scope=app,
        id=config.deployment.pipeline_stack_id,
        config=config,
        env=config.deployment.pipeline_environment.env
    )

    """
    =============================
    APP SYNTH - DONT COPY OR MOVE
    =============================
    """
    app.synth()
elif config.type == DeploymentType.UI_ONLY:
    print(f"Identified app type: {config.type}.")

    config = cast(ProvenaUIOnlyConfig, config)

    print(
        f"Config ID identified and validated successfully - running against {config_id = }.")

    # This app is for the ops deployment of STAGE
    app = cdk.App()

    """
    =========================
    DEPLOYMENT PIPELINE STACK
    =========================
    This should be the only stack in the deployment pipeline.
    """

    ProvenaUIOnlyPipelineStack(
        scope=app,
        id=config.pipeline_stack_id,
        config=config,
        env=config.aws_environment.env,
    )

    """
    =============================
    APP SYNTH - DONT COPY OR MOVE
    =============================
    """
    app.synth()
else: 
    raise ValueError(f"Unexpected DeploymentType in base config: {config.type}. Report to system administrator.")