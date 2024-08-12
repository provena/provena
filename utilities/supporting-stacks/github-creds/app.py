#!/usr/bin/env python3
import os

import aws_cdk as cdk

from github_creds.github_creds_stack import GithubCredsStack
from ProvenaSharedFunctionality.utils import perform_config_substitution
from pydantic import BaseModel


# define config class
class AWSTarget(BaseModel):
    account: str
    region: str

    @property
    def env(self) -> cdk.Environment:
        return cdk.Environment(account=self.account, region=self.region)


class GithubBootstrapConfig(BaseModel):
    env: AWSTarget
    github_token_arn: str


# Define method to load configs


app = cdk.App()
GithubCredsStack(
    app,
    "GithubCredsStack",
)

app.synth()
