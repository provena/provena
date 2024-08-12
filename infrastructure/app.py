#!/usr/bin/env python3
import aws_cdk as cdk
import os

"""
This python app just deploys the codebuild GitHub authentication stack.

Make sure that when tokens are expired that this underlying stack is also
redeployed.

The config is dispatched in a similar way to the main provena app config. 

Specify a PROVENA_CONFIG_ID environment variable which is available in the user
customised get_bootstrap_config map exported from configs.config_map
"""

app = cdk.App()

from provena.utility_stacks.CodeBuildGithubBootstrap import CodeBuildGithubBootstrap
from provena.config.config_loader import get_bootstrap_config

# Dispatch from config ID
# =========================

config_id = os.getenv("PROVENA_CONFIG_ID")

if config_id is None:
    raise ValueError("No PROVENA_CONFIG_ID environment variable provided.")

config_loader = get_bootstrap_config(config_id)
config = config_loader()

# Github bootstrap

# BUILD - comment when working on OPS

CodeBuildGithubBootstrap(
    scope=app, id='GithubCredsBootstrap', token_arn=config.github_token_arn, env=config.env)

# TODO bring back FeatureBranchManager and ExporterJob in a non specific config approach

# app synth
app.synth()
