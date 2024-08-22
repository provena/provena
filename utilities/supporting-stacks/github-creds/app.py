#!/usr/bin/env python3
import aws_cdk as cdk
from github_creds.github_creds_stack import GithubCredsStack
from config import retrieve_config

# get user to select a suitable config
config = retrieve_config()

app = cdk.App()

GithubCredsStack(app, "GithubCredsBootstrap", config.github_token_arn, env=config.env.env)

app.synth()
