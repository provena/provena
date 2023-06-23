from aws_cdk import (
    Stack,
    aws_codebuild as build,
    SecretValue
)

from typing import Any
from constructs import Construct


class CodeBuildGithubBootstrap(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            token_arn: str,
            **kwargs: Any) -> None:
        """
        __init__  

        Bootstraps the AWS target environment with CodeBuild github credentials.
        The specified token arn should be a secret manager secret with a Github
        OAuth token ARN with permissions to push/pull/admin hook to all repos
        required in the account.

        Parameters
        ----------
        scope : Construct
            CDK scope
        id : str
            The CDK stack ID
        token_arn : str
            The Oauth token secret manager ARN
        """
        super().__init__(scope, id, **kwargs)

        build.GitHubSourceCredentials(
            self, "CodeBuildGitHubCredentials",
            access_token=SecretValue.secrets_manager(token_arn)
        )
