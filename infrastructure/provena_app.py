#!/usr/bin/env python3
import aws_cdk as cdk
import os
from provena.config.config_class import ProvenaConfig
from provena.pipeline.pipeline_stack import ProvenaPipelineStack
from provena.config.config_helpers import validate_config
from configs.config_map import get_app_config
from typing import Optional

"""
This manages a provena app deployment. The config is dispatched based on the
config ID. This config ID must be present in the imported config map from
configs.config_map. This allows organisational extension of private
configurations while retaining a fully typed config interface.

How the user creates these config objects is open for developer preference. You
can instantiate them directly as a python object, or parse from a JSON object.
"""

# Dispatch from config ID
# =========================

config_id = os.getenv("PROVENA_CONFIG_ID")

if config_id is None:
    raise ValueError("No PROVENA_CONFIG_ID environment variable provided.")

get_config = get_app_config(config_id)

if get_config is None:
    raise ValueError(
        f"{config_id = } is not a valid config option according to the specified config map.")

assert get_config is not None

config = get_config()
assert config

# Validate imported config
# =========================

# Validate config
validate_config(config)

print(
    f"Config ID identified and validated successfully - deploying against {config_id = }.")

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
    env=config.deployment.pipeline_environment
)

"""
=============================
APP SYNTH - DONT COPY OR MOVE
=============================
"""
app.synth()
