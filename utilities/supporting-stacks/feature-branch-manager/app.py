#!/usr/bin/env python3
import aws_cdk as cdk
from feature_branch_manager.feature_branch_manager_stack import FeatureBranchManager
from config import retrieve_config

# get user to select a suitable config
config = retrieve_config()

app = cdk.App()

FeatureBranchManager(app, "feature-branch-manager", config=config, env=config.env.env)

app.synth()
