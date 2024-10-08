from aws_cdk import Stack, aws_codebuild as build, aws_lambda as _lambda, aws_iam as iam
from constructs import Construct
from config import FeatureBranchManagerConfig
from typing import Any, Dict
from feature_branch_manager.timed_lambda import TimedLambda

def create_plaintext_env_vars(
    config: FeatureBranchManagerConfig,
) -> Dict[str, build.BuildEnvironmentVariable]:
    """
    Automatically create plaintext environment variables from config attributes.

    Args:
        config: An instance of FeatureBranchManagerStackConfig.

    Returns:
        A dictionary of environment variable names to BuildEnvironmentVariable objects.
    """
    return {
        key.upper(): build.BuildEnvironmentVariable(
            type=build.BuildEnvironmentVariableType.PLAINTEXT,
            value=str(getattr(config, key)),
        )
        for key in vars(config)
        if key != "github_api_token_arn"
        and not callable(getattr(config, key))
    }


class FeatureBranchManager(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        config: FeatureBranchManagerConfig,
        **kwargs: Any,
    ) -> None:
        """
        Deploys a codebuild project and scheduled runner which sources the
        github repo off main and runs the feature branch cleanup script.


        Parameters
        ----------
        scope : Construct
            The CDK Scope
        id : str
            The construct ID
        """
        super().__init__(scope, id, **kwargs)

        # source this repo
        repo_source = build.Source.git_hub(
            owner=config.repo_owner,
            repo=config.repo_name,
            webhook=False,
            branch_or_ref=config.branch_name,
        )
        # Create the secret environment variable separately
        secret_env_vars: Dict[str, build.BuildEnvironmentVariable] = {
            "GITHUB_TOKEN": build.BuildEnvironmentVariable(
                type=build.BuildEnvironmentVariableType.SECRETS_MANAGER,
                value=config.github_api_token_arn,
            )
        }

        # Generate plaintext environment variables
        plaintext_env_vars: Dict[str, build.BuildEnvironmentVariable] = (
            create_plaintext_env_vars(config)
        )
        # Merge the dictionaries
        build_environment_variables: Dict[str, build.BuildEnvironmentVariable] = {
            **secret_env_vars,
            **plaintext_env_vars,
        }

        # make the codebuild project - this just runs the repo script
        project = build.Project(
            scope=self,
            id="project",
            source=repo_source,
            description="Runs the feature branch manager script - this build is scheduled.",
            environment=build.BuildEnvironment(
                build_image=build.LinuxBuildImage.AMAZON_LINUX_2_4,
                environment_variables=build_environment_variables,
            ),
            build_spec=build.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {"build": {"commands": [f"./{config.script_path}"]}},
                }
            ),
        )

        # setup timed lambda job to run it
        lambda_func = _lambda.Function(
            scope=self,
            id="runner",
            code=_lambda.Code.from_asset(path="feature_branch_manager/schedule_lambda"),
            handler="lambda_function.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            description="Triggers the CodeBuild project which runs the feature brach manager.",
            environment={"BUILD_PROJECT_NAME": project.project_name},
        )

        # midnight every day
        schedule_expression = "cron(0 0 * * ? *)"
        schedule_job = TimedLambda(
            scope=self,
            construct_id="runner-schedule",
            lambda_function=lambda_func,
            schedule_expression=schedule_expression,
        )

        # allow the lambda function to trigger the build project
        assert lambda_func.role
        lambda_func.role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["codebuild:StartBuild"],
                resources=[project.project_arn],
            )
        )

        # the codebuild project needs to be able to list, describe and delete cloudformation stacks
        project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStacks",
                    "cloudformation:DeleteStack",
                ],
                resources=["*"],
            )
        )
