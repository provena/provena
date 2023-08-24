from aws_cdk import (
    CfnOutput,
    Stack,
    pipelines as pipelines,
    aws_codepipeline as code_pipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_secretsmanager as sm,
    aws_codebuild as build,
    SecretValue,
    aws_iam as iam,
    SecretValue,
    ArnFormat,
    Annotations,
    aws_s3 as s3
)
from constructs import Construct
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.pipeline.deployment_stage import ProvenaDeploymentStage, ProvenaUIOnlyStage
from provena.custom_constructs.pipeline_event_processor import PipelineEventProcessor
from provena.custom_constructs.build_badge_lambda import BuildBadgeLambda
from provena.pipeline.testing_setup.testing_config import *
from provena.pipeline.testing_setup.testing_shell_steps import generate_unit_tests, generate_system_tests, generate_integration_tests
from provena.pipeline.testing_setup.type_checking_shell_step import generate_typescript_checking_step, generate_mypy_checking_step
from provena.config.config_class import *
from provena.config.config_helpers import resolve_endpoints
from provena.utility.cfn_output_helpers import get_output_name, get_stack_name
from typing import List, Dict

VERSION_INFO_FILE_PATH = "../repo-tools/github-version/version_info.json"


def create_artifact_bucket(scope: Construct, id: str) -> s3.Bucket:
    # creates a cleaned up auto deleting bucket
    return s3.Bucket(scope=scope, id=id, auto_delete_objects=True, removal_policy=RemovalPolicy.DESTROY)


def create_base_pipeline(scope: Construct, id: str) -> code_pipeline.Pipeline:
    artifact_bucket = create_artifact_bucket(scope=scope, id=f'{id}-artifacts')
    return code_pipeline.Pipeline(scope=scope, id=id, artifact_bucket=artifact_bucket)


class ProvenaPipelineStack(Stack):
    def __init__(self,
                 scope: Construct,
                 id: str,
                 config: ProvenaConfig,
                 **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # This construct deploys into the targeted environment (possibly
        # different to deployment environment) a configurable set of pipelines
        # and support infrastructure which deploys the Provena stack into the
        # deployment_environment. The deployment environment needs to have been
        # cross account CDK bootstrapped to trust the pipeline account.

        """
        =======================
        INFRASTRUCTURE PIPELINE
        =======================
        """

        # Expose the stage
        self.stage = config.deployment.stage

        # resolve the endpoints - this is used in UI build steps and is a critical process
        self.endpoints = resolve_endpoints(config=config)

        # This is a robot oauth which has access to repo
        o_auth_token = SecretValue.secrets_manager(
            config.deployment.github_token_arn)

        # Stack aware generation of secrets manager permission
        secrets_arn = Stack.of(self).format_arn(
            partition="aws",
            service="secretsmanager",
            resource="secret",
            resource_name="*",
            # Secrets have colon separator
            arn_format=ArnFormat.COLON_RESOURCE_NAME
        )
        secret_manager_policy = iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue",
                     "secretsmanager:DescribeSecret"],
            # policy can pull secrets from build account (current)
            resources=[
                secrets_arn
            ]
        )

        # S3 upload policy - enable building static websites into buckets
        # These are required for s3 sync - we don't know the bucket names
        # before deployment so we use a slightly more inclusive policy
        # make sure build processes are trusted
        bucket_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject",
                     "s3:ListBucket", "s3:DeleteObject",],
            resources=[
                "arn:aws:s3:::*"
            ],
            effect=iam.Effect.ALLOW
        )

        install_commands = [
            # use node 18
            "n 18"
        ]
        shared_synth_code_build_step_commands = [
            # node and npm version
            "node -v",
            "npm -v",
            # move to repo tooling
            "cd repo-tools/github-version",
            "pip install -r requirements.txt",
            # run get version info which writes to file
            f"python get_version_info.py {config.deployment.git_repo_string} $GIT_COMMIT_ID --export",
            "cd ../../infrastructure",
            # install jq for parsing file w version info
            "apt-get install jq",
            # Install cdk
            "npm install -g aws-cdk",
            # Install the pip dependencies
            "pip install -r requirements.txt",
            # read version info from file and export to env to be used in synth of pipeline stack
            ". scripts/export_version_info.sh",
            # Synthesize pipeline stack
            config.deployment.cdk_synth_command
        ]

        # Dockerhub creds setup for pipeline asset publishing
        dh_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='dh_secret',
            secret_complete_arn=config.general.dockerhub_creds_arn
        )
        # Pipelines connection
        dh_login = pipelines.DockerCredential.docker_hub(
            secret=dh_secret,
            secret_password_field="password",
            secret_username_field="username"
        )

        if config.deployment.cross_account or not config.deployment.feature_deployment:
            if config.deployment.cross_account:
                Annotations.of(self).add_warning(
                    "Since cross account deployment is required, artifact buckets cannot be self deleting...")
            else:
                Annotations.of(self).add_info(
                    "Since this is not a feature deployment, old style artifact buckets are used - these are encrypted...")

            github_source_synth = pipelines.CodePipelineSource.git_hub(
                repo_string=config.deployment.git_repo_string,
                branch=config.deployment.git_branch_name,
                authentication=o_auth_token,
                trigger=config.deployment.main_pipeline_trigger
            )

            deployment_pipeline = pipelines.CodePipeline(
                self, "fullpipe",
                
                # Tell pipeline to use docker login 
                docker_credentials=[dh_login],

                # Is this a cross account deployment?
                # If so we need to enable cross account keys
                # NOTE this will incur additional costs from KMS
                cross_account_keys=config.deployment.cross_account,

                # Enable docker
                docker_enabled_for_self_mutation=True,
                docker_enabled_for_synth=True,

                # Add s3 permissions for code build projects
                # //TODO investigate making this on a per step basis
                # we also need secret manager access for some integration/unit tests which use secrets
                code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[bucket_policy, secret_manager_policy]
                ),

                synth_code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[secret_manager_policy]
                ),

                synth=pipelines.CodeBuildStep("Synth",
                                              input=github_source_synth,
                                              commands=shared_synth_code_build_step_commands,
                                              # installs the node v18 runtime
                                              install_commands=install_commands,
                                              env={
                                                  "GIT_COMMIT_ID": github_source_synth.source_attribute("CommitId"),
                                                  "VERSION_INFO_FILE_PATH": VERSION_INFO_FILE_PATH,
                                              },
                                              primary_output_directory=f"infrastructure/{config.deployment.cdk_out_path}",
                                              build_environment=build.BuildEnvironment(
                                                  environment_variables={"github_oauth_token": build.BuildEnvironmentVariable(
                                                      value=config.deployment.github_token_arn,
                                                      type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
                                                  )}
                                              )
                                              )
            )
        else:  # not cross account and is feature deployment

            github_source_synth = pipelines.CodePipelineSource.git_hub(
                repo_string=config.deployment.git_repo_string,
                branch=config.deployment.git_branch_name,
                authentication=o_auth_token,
                trigger=pipeline_actions.GitHubTrigger.NONE
            )

            deployment_pipeline = pipelines.CodePipeline(
                self, "fullpipe",
                
                # Tell pipeline to use docker login 
                docker_credentials=[dh_login],

                # use a base pipeline so we have an artifact bucket
                code_pipeline=create_base_pipeline(scope=self, id='full'),

                # Enable docker
                docker_enabled_for_self_mutation=True,
                docker_enabled_for_synth=True,

                # Add s3 permissions for code build projects
                # //TODO investigate making this on a per step basis
                code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[bucket_policy, secret_manager_policy]
                ),

                synth_code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[secret_manager_policy]
                ),

                synth=pipelines.CodeBuildStep("Synth",
                                              input=github_source_synth,
                                              # installs the node v18 runtime
                                              install_commands=install_commands,
                                              commands=shared_synth_code_build_step_commands,
                                              env={
                                                  "GIT_COMMIT_ID": github_source_synth.source_attribute("CommitId"),
                                                  "VERSION_INFO_FILE_PATH": VERSION_INFO_FILE_PATH,
                                              },
                                              primary_output_directory=f"infrastructure/{config.deployment.cdk_out_path}",
                                              build_environment=build.BuildEnvironment(
                                                  environment_variables={"github_oauth_token": build.BuildEnvironmentVariable(
                                                      value=config.deployment.github_token_arn,
                                                      type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
                                                  )}
                                              )
                                              )
            )

        # Deploy infrastructure
        self.deployment = ProvenaDeploymentStage(
            self,
            "deploy",
            config=config,
        )

        # Determine shared library env requirements - still need to setup keycloak client ID for each static UI
        shared_lib_env_variables: Dict[str, str] = {
            "VITE_STAGE": self.stage,
            "VITE_THEME_ID": config.general.ui_theme_id,


            "VITE_WARMER_API_ENDPOINT": self.endpoints.warmer_api,
            "VITE_JOB_API_ENDPOINT": self.endpoints.async_jobs_api,
            "VITE_REGISTRY_API_ENDPOINT": self.endpoints.registry_api,
            "VITE_AUTH_API_ENDPOINT": self.endpoints.auth_api,
            "VITE_PROV_API_ENDPOINT": self.endpoints.prov_api,
            "VITE_SEARCH_API_ENDPOINT": self.endpoints.search_api,
            "VITE_DATA_STORE_API_ENDPOINT": self.endpoints.data_store_api,

            "VITE_LANDING_PAGE_LINK": self.endpoints.landing_ui,
            "VITE_DATA_STORE_LINK": self.endpoints.data_store_ui,
            "VITE_PROV_STORE_LINK": self.endpoints.prov_ui,
            "VITE_REGISTRY_LINK": self.endpoints.registry_ui,
            "VITE_DOCUMENTATION_BASE_LINK": config.general.documentation_base_link,
            "VITE_CONTACT_US_LINK":  config.general.contact_us_link,

            "VITE_KEYCLOAK_AUTH_ENDPOINT": self.endpoints.keycloak_minimal,
            "VITE_KEYCLOAK_REALM": self.endpoints.keycloak_realm_name
        }

        # Create the static website build steps
        static_shell_steps = self.create_static_build_list(
            shared_lib_env_variables=shared_lib_env_variables)

        """
        Ordering
        [pre] unit tests (optional)
        [deploy] deploy app
        [post]
        - integration tests (optional)
        - build and deploy websites
        - system tests (optional)
        """

        # Setup pre and post step sequences
        pre: List[pipelines.Step] = []
        post: List[pipelines.Step] = []

        # Add build steps
        post.extend(static_shell_steps)

        # Check activations on test stages based on deployment type
        test_config = config.tests
        ts_type_check_active = test_config.test_activation[TestType.TS_TYPE_CHECK]
        mypy_type_check_active = test_config.test_activation[TestType.MYPY_TYPE_CHECK]
        unit_active = test_config.test_activation[TestType.UNIT]
        integration_active = test_config.test_activation[TestType.INTEGRATION]
        system_active = test_config.test_activation[TestType.SYSTEM]

        # Are type checks required? Pre test before deployment
        if ts_type_check_active:
            ts_type_check_step = generate_typescript_checking_step(
                id="ts-type-check")
            pre.append(ts_type_check_step)
        if mypy_type_check_active:
            mypy_type_check_step = generate_mypy_checking_step(
                id="mypy-type-check")
            pre.append(mypy_type_check_step)

        # Unit tests, general_config=config.general
        # these come first if active
        if unit_active:
            unit_test_step = generate_unit_tests(
                id='unit',
                config=config
            )
            pre.append(unit_test_step)

        # Integration tests
        if integration_active:
            integration_test_step = generate_integration_tests(
                id='integration',
                config=config,
                # data store api endpoint
                data_store_api_endpoint=self.deployment.data_api_endpoint,
                # registry_api_endpoint
                registry_api_endpoint=self.deployment.registry_api_endpoint,
                # /realms/realm_name form
                keycloak_endpoint=self.deployment.keycloak_auth_endpoint_cfn_output,
                prov_api_endpoint=self.deployment.prov_api_endpoint,
                auth_api_endpoint=self.deployment.auth_api_endpoint,
                job_api_endpoint=self.deployment.job_api_endpoint
            )
            post.append(integration_test_step)
            # integration test first then build
            for step in static_shell_steps:
                step.add_step_dependency(integration_test_step)

        # System tests
        if system_active:
            # system tests can only run if UIs are deployed (data store and landing portal)
            #! TODO parameterise these tests per UI

            # data store
            assert config.components.data_store
            assert self.deployment.data_store_url

            # landing page
            assert config.components.landing_page
            assert self.deployment.landing_portal_url

            system_test_step = generate_system_tests(
                id="system",
                config=config,
                data_store_url=self.deployment.data_store_url,
                landing_portal_url=self.deployment.landing_portal_url
            )
            post.append(system_test_step)
            # ensure system tests occur after static build deploys
            for step in static_shell_steps:
                system_test_step.add_step_dependency(step)

        # Add to pipeline
        deployment_pipeline.add_stage(
            self.deployment,
            pre=pre,
            post=post
        )

        # build pipeline so that underlying object is resolved
        deployment_pipeline.build_pipeline()

        """
        =====================
        QUICK DEPLOY PIPELINE
        =====================
        """

        if config.deployment.quick_deploy_pipeline:

            github_source_synth = pipelines.CodePipelineSource.git_hub(
                repo_string=config.deployment.git_repo_string,
                branch=config.deployment.git_branch_name,
                authentication=o_auth_token,
                trigger=pipeline_actions.GitHubTrigger.NONE
            )

            quick_deploy_pipeline = pipelines.CodePipeline(
                self, "quickpipe",
                
                # Tell pipeline to use docker login 
                docker_credentials=[dh_login],

                # use a base pipeline so we have an artifact bucket
                code_pipeline=create_base_pipeline(
                    scope=self, id='quick-deploy'),

                # Enable docker
                docker_enabled_for_self_mutation=True,
                docker_enabled_for_synth=True,

                # Add s3 permissions for code build projects
                # //TODO investigate making this on a per step basis
                code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[bucket_policy, secret_manager_policy]
                ),

                synth_code_build_defaults=pipelines.CodeBuildOptions(
                    role_policy=[secret_manager_policy]
                ),

                synth=pipelines.CodeBuildStep("Synth",
                                              input=github_source_synth,
                                              install_commands=install_commands,
                                              commands=shared_synth_code_build_step_commands,
                                              env={
                                                  "GIT_COMMIT_ID": github_source_synth.source_attribute("CommitId"),
                                                  "VERSION_INFO_FILE_PATH": VERSION_INFO_FILE_PATH,
                                              },
                                              primary_output_directory=f"infrastructure/{config.deployment.cdk_out_path}",
                                              build_environment=build.BuildEnvironment(
                                                  environment_variables={"github_oauth_token": build.BuildEnvironmentVariable(
                                                      value=config.deployment.github_token_arn,
                                                      type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
                                                  )}
                                              )
                                              )
            )

            # Add to pipeline
            quick_deploy_pipeline.add_stage(
                self.deployment,
            )

            quick_deploy_pipeline.build_pipeline()

        """
        ===================================
        INTERFACE AND MODEL EXPORT PIPELINE
        ===================================
        """

        if config.deployment.interface_pipeline:
            interface_pipeline = code_pipeline.Pipeline(
                scope=self,
                id="interface-pipe",
                artifact_bucket=create_artifact_bucket(
                    scope=self, id='interface-artifacts') if config.deployment.feature_deployment else None,
            )
            # Source repo
            source_artifact = code_pipeline.Artifact("source")
            source_stage: code_pipeline.IStage = interface_pipeline.add_stage(
                stage_name="Source-repo")
            source_stage.add_action(
                pipeline_actions.GitHubSourceAction(
                    oauth_token=o_auth_token,
                    output=source_artifact,
                    owner=config.deployment.git_owner_org,
                    repo=config.deployment.git_repo_name,
                    branch=config.deployment.git_branch_name,
                    trigger=config.deployment.interface_pipeline_trigger_settings,
                    action_name="Source-repository"
                )
            )

            # Run interface export
            # Define a code build project to do it
            project = build.Project(
                scope=self,
                id='interface-export',

                # badge=True,
                environment=build.BuildEnvironment(
                    environment_variables={
                        "OAUTH_TOKEN": build.BuildEnvironmentVariable(
                            value=config.deployment.github_token_arn,
                            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
                        )
                    },
                    build_image=build.LinuxBuildImage.STANDARD_5_0
                ),
                build_spec=build.BuildSpec.from_object(
                    {
                        "version": "0.2",
                        "phases": {
                            "build": {
                                "commands": [
                                    # Setup git identity
                                    "git config --global user.email \"interface.export@fake.com\"",
                                    "git config --global user.name \"Interface Export Bot\"",
                                    # Clone repo
                                    f"git clone https://int-export-build:${{OAUTH_TOKEN}}@github.com/{config.deployment.git_repo_string}.git",
                                    f"cd {config.deployment.git_repo_name}",
                                    f"git checkout {config.deployment.git_branch_name}",
                                    # Run the interface export
                                    f"./{INTERFACE_EXPORT_SCRIPT_LOCATION}",
                                    # Commit changes from interface export
                                    "git commit -am \"Updating interfaces (codebuild auto)\" || echo \"Commit failed, no changes or other issue.\"",
                                    # Push changes
                                    "git push || echo \"Git push not required and/or failed\"",
                                    # Run the model export
                                    f"./{MODEL_EXPORT_SCRIPT_LOCATION}",
                                    # Commit changes from model export
                                    "git commit -am \"Updating model exports (codebuild auto)\" || echo \"Commit failed, no changes or other issue.\"",
                                    # Push changes
                                    "git push || echo \"Git push not required and/or failed\""
                                ]
                            }
                        }
                    }
                )
            )

            # Produce action to export interfaces and
            # add to new stage
            export_action = pipeline_actions.CodeBuildAction(
                input=source_artifact,
                project=project,
                action_name="Export-interfaces-and-models"
            )
            export_stage = interface_pipeline.add_stage(
                stage_name="Export-interface-and-models")
            export_stage.add_action(
                export_action
            )

            # Trigger deployment pipeline
            trigger_project = build.Project(
                scope=self,
                id='trigger-codebuild',

                # badge=True,
                environment=build.BuildEnvironment(
                    build_image=build.LinuxBuildImage.STANDARD_5_0,
                    environment_variables={
                        "PIPELINE_NAME": build.BuildEnvironmentVariable(
                            value=deployment_pipeline.pipeline.pipeline_name,
                            type=build.BuildEnvironmentVariableType.PLAINTEXT)
                    }
                ),
                build_spec=build.BuildSpec.from_object(
                    {
                        "version": "0.2",
                        "phases": {
                            "build": {
                                "commands": [
                                    "echo \"Triggering pipeline on behalf of user after interface and model export.\"",
                                    "aws codepipeline start-pipeline-execution --name ${PIPELINE_NAME}",
                                    "echo \"Complete\""
                                ]
                            }
                        }
                    }
                )
            )
            # Allow execution start
            trigger_project.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["codepipeline:StartPipelineExecution"],
                    resources=[deployment_pipeline.pipeline.pipeline_arn]
                )
            )

            # Add a trigger which triggers the deployment pipeline
            # corresponding to this stage

            # Run only after export interface finishes
            trigger_action = pipeline_actions.CodeBuildAction(
                input=source_artifact,
                project=trigger_project,
                action_name="Trigger-deployment-pipeline",
                run_order=2
            )
            export_stage.add_action(
                trigger_action
            )

        """
        ==============================
        UI BUILD ONLY UTILITY PIPELINE
        ==============================
        """
        if config.deployment.ui_only_pipeline:
            ui_pipeline = code_pipeline.Pipeline(
                scope=self,
                id="ui-only-pipe",
                artifact_bucket=create_artifact_bucket(
                    scope=self, id='uionly-artifacts') if config.deployment.feature_deployment else None,
            )

            # Source repo
            source_artifact = code_pipeline.Artifact("source")
            ui_only_source_stage: code_pipeline.IStage = ui_pipeline.add_stage(
                stage_name="Source-repo")
            ui_only_source_stage.add_action(
                pipeline_actions.GitHubSourceAction(
                    oauth_token=o_auth_token,
                    output=source_artifact,
                    owner=config.deployment.git_owner_org,
                    repo=config.deployment.git_repo_name,
                    branch=config.deployment.git_branch_name,
                    trigger=config.deployment.ui_pipeline_trigger_settings,
                    action_name="Source-repository"
                )
            )

            # deploy actions
            deploy_action_list = self.create_static_build_list_codebuild(
                source_artifact=source_artifact,
                shared_lib_env_variables=shared_lib_env_variables
            )

            ui_build_stage = ui_pipeline.add_stage(
                stage_name="Build-UIs")
            for action in deploy_action_list:
                ui_build_stage.add_action(action)

        """
        =========================
        PIPELINE ASSOCIATED INFRA
        =========================
        """

        # Get the underlying pipeline object and add notifications on all stages

        # Cannot edit this
        finalized_code_pipeline = deployment_pipeline.pipeline

        if config.deployment.email_alerts_activated:
            if not config.deployment.pipeline_alert_email:
                Annotations.of(self).add_error(
                    "Cannot have pipeline alerts without specifying email. Aborting.")
                raise ValueError()

            # Build filtered topic to email
            PipelineEventProcessor(
                scope=self,
                construct_id="pipeline-event-processor",
                code_pipeline=finalized_code_pipeline,
                email_address=config.deployment.pipeline_alert_email
            )

        if config.deployment.build_badge:
            build_badge_config = config.deployment.build_badge

            # Add build badge support
            allocator = DNSAllocator(
                scope=self,
                construct_id='allocator',
                hosted_zone_id=config.dns.hosted_zone_id,
                hosted_zone_name=config.dns.hosted_zone_name,
            )
            BuildBadgeLambda(
                scope=self,
                construct_id='deployment-build-badge',
                domain=build_badge_config.build_domain,
                stage=config.deployment.stage,
                cert_arn=config.dns.domain_certificate_arn,
                allocator=allocator,
                built_pipeline=finalized_code_pipeline
            )

            # add build badge for interface exports
            if config.deployment.interface_pipeline:
                BuildBadgeLambda(
                    scope=self,
                    construct_id='interface-build-badge',
                    domain=build_badge_config.interface_domain,
                    stage=config.deployment.stage,
                    cert_arn=config.dns.domain_certificate_arn,
                    allocator=allocator,
                    built_pipeline=interface_pipeline
                )

        """
        =================================
        CONTINUOUS INTEGRATION CODEBUILDS
        =================================

        Runs mypy type checks, ts type checks, and unit tests on CodeBuild, triggered by PRs into 
        the current stage's branch.
        The status of the checks/tests are included in the PR.

        """

        if config.deployment.ci_hook_pr_into_branch:
            # Github source code for ci_projects and define triggers for the build.
            # Credentials are CodeBuild wide for GitHub.
            branch_name = config.deployment.git_branch_name
            stage = config.deployment.stage
            github_source = build.Source.git_hub(
                owner=config.deployment.git_owner_org,
                repo=config.deployment.git_repo_name,
                clone_depth=1,
                report_build_status=True,
                webhook_filters=[
                    # trigger for new PRs on this stage's branch
                    build.FilterGroup.in_event_of(
                        build.EventAction.PULL_REQUEST_CREATED).and_base_branch_is(branch_name),
                    # trigger for updates (new commits) to existing PRs into this stage's branch
                    build.FilterGroup.in_event_of(
                        build.EventAction.PULL_REQUEST_UPDATED).and_base_branch_is(branch_name),
                    # trigger for reopening PRs into this stage's branches
                    build.FilterGroup.in_event_of(
                        build.EventAction.PULL_REQUEST_REOPENED).and_base_branch_is(branch_name),
                ],
            )
            # code build project for CI mypy
            ci_project_mypy = build.Project(
                scope=self,
                id="ci_mypy_type_check",
                project_name=f"{stage}MypyTypeCheck",
                source=github_source,
                badge=True,
                build_spec=build.BuildSpec.from_object(
                    {
                        "version": "0.2",
                        "phases": {
                            "build": {
                                "commands": [
                                    'echo "Running mypy type checks"',
                                    f"./{MYPY_TYPE_CHECKING_SCRIPT_LOCATION}",
                                ]
                            }
                        }
                    },
                ),
                description="Run mypy type checks triggered by PRs",
                environment=build.BuildEnvironment(
                    build_image=build.LinuxBuildImage.STANDARD_5_0
                ),
            )

            # code build project for CI typescript tests
            ci_project_ts_type = build.Project(
                scope=self,
                id="ci_ts_type_check",
                project_name=f"{stage}TypescriptTypeCheck",
                source=github_source,
                badge=True,
                build_spec=build.BuildSpec.from_object(
                    {
                        "version": "0.2",
                        "phases": {
                            "build": {
                                "commands": [
                                    'echo "Running ts type checking triggered by PRs"',
                                    f"./{TS_TYPE_CHECKING_SCRIPT_LOCATION}",
                                ]
                            }
                        }
                    },
                ),
                description="Run ts type checks on PRs",
                environment=build.BuildEnvironment(
                    build_image=build.LinuxBuildImage.STANDARD_5_0
                ),
            )

            # code build project for CI unit tests
            assert config.tests.unit_tests, "Need unit test config for ci hooks"
            ci_project_unit_tests = build.Project(
                scope=self,
                id="ci_unit_test",
                project_name=f"{stage}UnitTests",
                source=github_source,
                badge=True,
                build_spec=build.BuildSpec.from_object(
                    {
                        "version": "0.2",
                        "phases": {
                            "build": {
                                "commands": [
                                    'echo "Running unit tests"',
                                    f"./{UNIT_TEST_SCRIPT}",
                                ]
                            }
                        }
                    },
                ),
                description="Run unit tests triggered by PRs",
                environment=build.BuildEnvironment(
                    environment_variables=generate_unit_secret_env_vars(
                        config=config.tests.unit_tests, general_config=config.general),
                    # some unit tests require docker.
                    privileged=True,
                    build_image=build.LinuxBuildImage.STANDARD_5_0
                ),
            )

            # grant secret read for handle credentials TODO don't assert this - but
            # would require parameterising the ID service unit tests
            assert config.components.identity_service
            handle_secret = sm.Secret.from_secret_complete_arn(
                scope=self,
                id='handle-creds-secret',
                secret_complete_arn=config.components.identity_service.handle_credentials_arn
            )
            handle_secret.grant_read(ci_project_unit_tests)

    def create_static_build_list(self, shared_lib_env_variables: Dict[str, str]) -> List[pipelines.ShellStep]:
        """    create_static_build_list
            Creates a list of shell steps for use in the pipeline.
            This is for building static websites.
            As you add static website builds, add to the list below.

            Returns
            -------
             : List[pipelines.ShellStep]
                The list of build steps to be added to pipeline.

            Raises
            ------
            Exception
                When you try to call without the deployment stage being in
                namespace will cause error.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        if (not self.deployment):
            raise Exception(
                "Called static build list before defining provena_deployment stage.")

        build_steps = []

        data_store_env_base = {k: v for k,
                               v in shared_lib_env_variables.items()}
        data_store_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "data-store-ui"
            }
        )

        # Add the static UI page builds to pipeline as post step
        build_steps.append(
            generate_react_static_shell_step(
                id="data-store-ui",
                working_dir="data-store-ui",
                bucket_name_cfn_output=self.deployment.data_store_ui_bucket_name,
                standard_env_variables=data_store_env_base,
            )
        )

        registry_env_base = {k: v for k,
                             v in shared_lib_env_variables.items()}
        registry_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "entity-registry-ui"
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="registry-ui",
                working_dir="registry-ui",
                bucket_name_cfn_output=self.deployment.registry_ui_bucket_name,
                standard_env_variables=registry_env_base,
            )
        )

        prov_ui_env_base = {k: v for k,
                            v in shared_lib_env_variables.items()}
        prov_ui_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "provenance-store-ui"
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="prov-ui",
                working_dir="prov-ui",
                bucket_name_cfn_output=self.deployment.prov_ui_bucket_name,
                standard_env_variables=prov_ui_env_base,
            )
        )

        landing_portal_env_base = {k: v for k,
                                   v in shared_lib_env_variables.items()}
        landing_portal_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "landing-portal-ui",
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="landing-portal-ui",
                working_dir="landing-portal-ui",
                bucket_name_cfn_output=self.deployment.landing_page_ui_bucket_name,
                standard_env_variables=landing_portal_env_base,
            )
        )

        return build_steps

    def create_static_build_list_codebuild(self, source_artifact: code_pipeline.Artifact, shared_lib_env_variables: Dict[str, str]) -> List[pipeline_actions.CodeBuildAction]:
        """    create_static_build_list_codebuild
            This method is a helper function used to build code pipeline BuildAction friendly
            build actions. 
            The difference between this and the above action is that we are not in the 
            cdk.pipelines abstracted environment meaning we don't have access to the 
            nice management of CfnOutputs that cdk pipelines provides. So here, we can 
            use a similar interface, but need to define it ourselves, in this case 
            using the AWS CLI to describe the stack. 

            Arguments
            ----------
            source_artifact : code_pipeline.Artifact
                The github source object - required for producing the code build action.

            Returns
            -------
             : List[pipeline_actions.CodeBuildAction]
                The list of actions which can be added to a stage.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        build_steps = []

        data_store_env_base = {k: v for k,
                               v in shared_lib_env_variables.items()}
        data_store_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "data-store-ui"
            }
        )

        # Add the static UI page builds to pipeline as post step
        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-data-store",
                source_artifact=source_artifact,
                working_dir="data-store-ui",
                # Normal variables at deploy time
                standard_env_variables=data_store_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.data_store_ui_bucket_name,
                }
            )
        )

        registry_env_base = {k: v for k,
                             v in shared_lib_env_variables.items()}
        registry_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "entity-registry-ui"
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-registry",
                source_artifact=source_artifact,
                working_dir="registry-ui",
                # Normal variables at deploy time
                standard_env_variables=registry_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.registry_ui_bucket_name,
                }
            )
        )

        prov_ui_env_base = {k: v for k,
                            v in shared_lib_env_variables.items()}
        prov_ui_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "provenance-store-ui"
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-prov",
                source_artifact=source_artifact,
                working_dir="prov-ui",
                # Normal variables at deploy time
                standard_env_variables=prov_ui_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.prov_ui_bucket_name,
                }
            )
        )

        landing_portal_env_base = {k: v for k,
                                   v in shared_lib_env_variables.items()}
        landing_portal_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "landing-portal-ui",
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-landing-portal",
                source_artifact=source_artifact,
                working_dir="landing-portal-ui",
                standard_env_variables=landing_portal_env_base,
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.landing_page_ui_bucket_name,
                }
            )
        )

        return build_steps


def generate_react_static_shell_step(
    id: str,
    working_dir: str,
    bucket_name_cfn_output: CfnOutput,
    standard_env_variables: Dict[str, str] = {},
    other_environment_cfn_outputs: Dict[str, CfnOutput] = {}
) -> pipelines.ShellStep:
    """    generate_react_static_shell_step
        Given some information, will produce a shell step which can be added
        as post step to deployment stage designed to build and deploy static
        websites from react project into s3 bucket.

        Arguments
        ----------
        id : str
            The construct id to use for the shell step
        working_dir : str
            The working directory of the UI project e.g. data-store-ui
        bucket_name_cfn_output : CfnOutput
            The cfn output which holds the bucket name to deploy into
        standard_env_variables : Optional[Dict[Str, Str]]
            Any environment variables you want to add which are resolvable at synthesis time
            i.e. static known string values - not properties of deploy time resources
        other_environment_cfn_outputs : Optional[Dict[Str, CfnOutput]]
            Any other cfn output variables you want to add e.g. api endpoints etc.

        Returns
        -------
         : pipelines.ShellStep
            The shell step which deploys the static site.
            needs to be added to pipeline.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # add the working directory env variable
    # for the build script
    standard_envs: Dict[str, str] = {
        "WORKING_DIRECTORY": working_dir
    }
    standard_envs.update(standard_env_variables)

    # convert standard envs to build environment vars
    build_vars = {key: build.BuildEnvironmentVariable(
        value=value, type=build.BuildEnvironmentVariableType.PLAINTEXT) for key, value in standard_envs.items()}

    # add bucket name to the cfn outputs
    cfn_envs = {"BUCKET_NAME": bucket_name_cfn_output}
    cfn_envs.update(other_environment_cfn_outputs)

    build_step = pipelines.CodeBuildStep(
        id=id,

        # what commands should be run?
        commands=[
            f"./{STATIC_BUILD_SCRIPT_LOCATION}"
        ],

        # Resolvable after deployment
        env_from_cfn_outputs=cfn_envs,

        # Statically resolvable
        build_environment=build.BuildEnvironment(
            environment_variables=build_vars
        ),

        # add build spec configuration to use bash shell
        partial_build_spec=build.BuildSpec.from_object(
            value={
                "env": {
                    "shell": "bash"
                }
            }
        )
    )

    return build_step


def generate_codebuild_static_action(
    scope: Construct,
    id: str,
    source_artifact: code_pipeline.Artifact,
    working_dir: str,
    standard_env_variables: Dict[str, str] = {
    },
    cfn_output_name_key: Dict[str, CfnOutput] = {}
) -> pipeline_actions.CodeBuildAction:
    """    generate_codebuild_static_action
        Generates a code_pipeline CodeBuildAction designed to build and
        upload to S3 a react front end. 
        This is different to the above method as it cannot use the abstracted
        stack aware environment of the cdk.pipelines library. We have to do 
        more manual hackery to get the cloud formation deploy time outputs 
        such as endpoint names etc.

        Arguments
        ----------
        scope : Construct
            CDK scope
        id : str
            CDK ID also used as the action name
        source_artifact : code_pipeline.Artifact
            The github source action
        working_dir : str
            The infrastructure working directory in repo
        standard_env_variables : Dict[str, str], optional
            Standard non deploy time static env vars, by default { }
        cfn_output_name_key : Dict[str, CfnOutput], optional
            A map of env variable name -> cloud formation output
            lookup key. The keys are defined by the id of the 
            CfnOutput object without underscores.

        Returns
        -------
         : pipeline_actions.CodeBuildAction
            The code build action which can be added into the 
            stage of the CodePipeline.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Add the working directory as a plaintext variable
    env: Dict[str, build.BuildEnvironmentVariable] = {
        "WORKING_DIRECTORY": build.BuildEnvironmentVariable(
            value=working_dir,
            type=build.BuildEnvironmentVariableType.PLAINTEXT
        )
    }

    # pull out std env variables
    for key, val in standard_env_variables.items():
        env[key] = build.BuildEnvironmentVariable(
            value=val,
            type=build.BuildEnvironmentVariableType.PLAINTEXT
        )

    # read dynamic cfn output commands
    command_list: List[str] = []

    for env_var_name, cfn_output in cfn_output_name_key.items():
        cfn_output_key = get_output_name(cfn_output)
        stack_name = get_stack_name(cfn_output)
        command_list.append(
            f"echo \"Retrieving variable with key {cfn_output_key} from stack {stack_name}\""
        )
        command_list.extend([
            # Get the variable from stack
            f"export {env_var_name}=$(aws cloudformation describe-stacks --stack-name {stack_name} --query \"Stacks[0].Outputs[?OutputKey=='{cfn_output_key}'].OutputValue\" --output text)",
            # if null - then exit - this prevents deployment if missing variables
            f'if [ -z ${env_var_name} ]; then exit 1; else echo "Variable retrieved successfully."; fi'
        ]
        )

    command_list.extend([
        'echo "Initiating build script"',
        f"./{STATIC_BUILD_SCRIPT_LOCATION}"
    ])

    # Define a code build project to do it
    project = build.Project(
        scope=scope,
        id=id,
        environment=build.BuildEnvironment(
            build_image=build.LinuxBuildImage.STANDARD_5_0,
            environment_variables=env
        ),
        build_spec=build.BuildSpec.from_object(
            {
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": command_list
                    }
                }
            }
        )
    )

    # Add permission to describe stack output variables
    project.add_to_role_policy(iam.PolicyStatement(
        actions=["cloudformation:DescribeStacks"],
        resources=["arn:aws:cloudformation:*:*:stack/*"]
    ))

    # Add permission to upload to S3 buckets for website builds
    project.add_to_role_policy(iam.PolicyStatement(
        actions=["s3:GetObject", "s3:PutObject",
                 "s3:ListBucket", "s3:DeleteObject"],
        resources=[
            "arn:aws:s3:::*"
        ],
        effect=iam.Effect.ALLOW
    ))

    # Produce action to build static front end
    return pipeline_actions.CodeBuildAction(
        input=source_artifact,
        project=project,
        action_name=id
    )


class ProvenaUIOnlyPipelineStack(Stack):
    def __init__(self,
                 scope: Construct,
                 id: str,
                 config: ProvenaUIOnlyConfig,
                 **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        """
        =======================
        INFRASTRUCTURE PIPELINE
        =======================
        """

        # Expose the stage
        self.stage = config.target_stage

        # expose config
        self.config = config

        # This is a robot oauth which has access to repo
        o_auth_token = SecretValue.secrets_manager(
            config.github_token_arn)

        # Stack aware generation of secrets manager permission
        secrets_arn = Stack.of(self).format_arn(
            partition="aws",
            service="secretsmanager",
            resource="secret",
            resource_name="*",
            # Secrets have colon separator
            arn_format=ArnFormat.COLON_RESOURCE_NAME
        )
        secret_manager_policy = iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            # policy can pull secrets from build account (current)
            resources=[
                secrets_arn
            ]
        )

        # S3 upload policy - enable building static websites into buckets
        # These are required for s3 sync - we don't know the bucket names
        # before deployment so we use a slightly more inclusive policy
        # make sure build processes are trusted
        bucket_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:DeleteObject",
                     "s3:PutObject", "s3:ListBucket"],
            resources=[
                "arn:aws:s3:::*"
            ],
            effect=iam.Effect.ALLOW
        )

        install_commands = [
            # use node 18
            "n 18"
        ]


        # Dockerhub creds setup for pipeline asset publishing
        dh_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='dh_secret',
            secret_complete_arn=config.dockerhub_creds_arn
        )
        # Pipelines connection
        dh_login = pipelines.DockerCredential.docker_hub(
            secret=dh_secret,
            secret_password_field="password",
            secret_username_field="username"
        )

        deployment_pipeline = pipelines.CodePipeline(
            self, "fullpipe",

            # Tell pipeline to use docker login 
            docker_credentials=[dh_login],

            # use a base pipeline so we have an artifact bucket
            code_pipeline=create_base_pipeline(scope=self, id='full'),

            # Add s3 permissions for code build projects
            # //TODO investigate making this on a per step basis
            code_build_defaults=pipelines.CodeBuildOptions(
                role_policy=[bucket_policy]
            ),

            synth_code_build_defaults=pipelines.CodeBuildOptions(
                role_policy=[secret_manager_policy]
            ),

            synth=pipelines.ShellStep("Synth",
                                      input=pipelines.CodePipelineSource.git_hub(
                                          repo_string=config.git_repo_string,
                                          branch=config.git_branch_name,
                                          authentication=o_auth_token,
                                          trigger=pipeline_actions.GitHubTrigger.NONE
                                      ),
                                      install_commands=install_commands,
                                      commands=[
                                          # Install cdk
                                          "npm install -g aws-cdk",
                                          # Move into infrastructure folder
                                          "cd infrastructure",
                                          # Install the pip dependencies
                                          "pip install -r requirements.txt",
                                          # Synthesize pipeline stack
                                          config.cdk_synth_command
                                      ],
                                      primary_output_directory=f"infrastructure/{config.cdk_out_path}"
                                      )
        )

        # Deploy infrastructure
        self.deployment = ProvenaUIOnlyStage(
            self,
            "deploy",
            config=config,
        )

        # Helpers to establish shared lib environment variables

        def create_full_url(sub: str, root: str) -> str:
            if sub == "":
                return f"https://{root}"
            else:
                return f"https://{sub}.{root}"

        landing_page_url = create_full_url(
            self.config.domains.landing_page_sub_domain,
            self.config.domains.root_domain
        )
        data_store_url = create_full_url(
            self.config.domains.data_store_sub_domain,
            self.config.domains.root_domain
        )
        registry_url = create_full_url(
            self.config.domains.registry_sub_domain,
            self.config.domains.root_domain
        )
        prov_store_url = create_full_url(
            self.config.domains.prov_store_sub_domain,
            self.config.domains.root_domain
        )

        shared_lib_env_variables: Dict[str, str] = {
            "VITE_STAGE": self.stage,
            "VITE_THEME_ID": self.config.ui_theme_id,

            "VITE_WARMER_API_ENDPOINT": self.config.domains.warmer_api_endpoint,
            "VITE_JOB_API_ENDPOINT": self.config.domains.async_jobs_api_endpoint,
            "VITE_REGISTRY_API_ENDPOINT": self.config.domains.registry_api_endpoint,
            "VITE_AUTH_API_ENDPOINT": self.config.domains.auth_api_endpoint,
            "VITE_PROV_API_ENDPOINT": self.config.domains.prov_api_endpoint,
            "VITE_SEARCH_API_ENDPOINT": self.config.domains.search_api_endpoint,
            "VITE_DATA_STORE_API_ENDPOINT": self.config.domains.data_api_endpoint,

            "VITE_LANDING_PAGE_LINK": landing_page_url,
            "VITE_DATA_STORE_LINK": data_store_url,
            "VITE_PROV_STORE_LINK":  prov_store_url,
            "VITE_REGISTRY_LINK": registry_url,

            "VITE_DOCUMENTATION_BASE_LINK": self.config.domains.documentation_base_link,
            "VITE_CONTACT_US_LINK":  self.config.domains.contact_us_link,

            "VITE_DOCUMENTATION_BASE_LINK": self.config.domains.documentation_base_link,
            "VITE_CONTACT_US_LINK":  self.config.domains.contact_us_link,

            "VITE_KEYCLOAK_AUTH_ENDPOINT": self.config.domains.keycloak_minimal_endpoint,
            "VITE_KEYCLOAK_REALM": self.config.domains.keycloak_realm_name
        }

        # Create the static website build steps
        static_shell_steps = self.create_static_build_list(
            shared_lib_env_variables=shared_lib_env_variables)

        """
        Ordering
        [pre] unit tests (optional)
        [deploy] deploy app
        [post]
        - integration tests (optional)
        - build and deploy websites
        - system tests (optional)
        """

        # Setup pre and post step sequences
        pre: List[pipelines.Step] = []
        post: List[pipelines.Step] = []

        # Add build steps
        post.extend(static_shell_steps)

        # Check activations on test stages based on deployment type
        ts_type_check_step = generate_typescript_checking_step(
            id="ts-type-check")
        pre.append(ts_type_check_step)

        # Add to pipeline
        deployment_pipeline.add_stage(
            self.deployment,
            pre=pre,
            post=post
        )

        # build pipeline so that underlying object is resolved
        deployment_pipeline.build_pipeline()

        """
        ===================================
        INTERFACE AND MODEL EXPORT PIPELINE
        ===================================
        """

        interface_pipeline = code_pipeline.Pipeline(
            scope=self,
            id="interface-pipe",
            artifact_bucket=create_artifact_bucket(
                scope=self, id='interface-artifacts')
        )

        # Source repo
        source_artifact = code_pipeline.Artifact("source")
        source_stage: code_pipeline.IStage = interface_pipeline.add_stage(
            stage_name="Source-repo")
        source_stage.add_action(
            pipeline_actions.GitHubSourceAction(
                oauth_token=o_auth_token,
                output=source_artifact,
                owner=config.git_owner_org,
                repo=config.git_repo_name,
                branch=config.git_branch_name,
                trigger=pipeline_actions.GitHubTrigger.NONE,
                action_name="Source-repository"
            )
        )

        # Run interface export
        # Define a code build project to do it
        project = build.Project(
            scope=self,
            id='interface-export',

            # badge=True,
            environment=build.BuildEnvironment(
                environment_variables={
                    "OAUTH_TOKEN": build.BuildEnvironmentVariable(
                        value=config.github_token_arn,
                        type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
                    )
                },
                build_image=build.LinuxBuildImage.STANDARD_5_0
            ),
            build_spec=build.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "build": {
                            "commands": [
                                # Setup git identity
                                "git config --global user.email \"interface.export@fake.com\"",
                                "git config --global user.name \"Interface Export Bot\"",
                                # Clone repo
                                f"git clone https://int-export-build:${{OAUTH_TOKEN}}@github.com/{config.git_repo_string}.git",
                                f"cd {config.git_repo_name}",
                                f"git checkout {config.git_branch_name}",
                                # Run the interface export
                                f"./{INTERFACE_EXPORT_SCRIPT_LOCATION}",
                                # Commit changes from interface export
                                "git commit -am \"Updating interfaces (codebuild auto)\" || echo \"Commit failed, no changes or other issue.\"",
                                # Push changes
                                "git push || echo \"Git push not required and/or failed\"",
                                # Run the model export
                                f"./{MODEL_EXPORT_SCRIPT_LOCATION}",
                                # Commit changes from model export
                                "git commit -am \"Updating model exports (codebuild auto)\" || echo \"Commit failed, no changes or other issue.\"",
                                # Push changes
                                "git push || echo \"Git push not required and/or failed\""
                            ]
                        }
                    }
                }
            )
        )

        # Produce action to export interfaces and
        # add to new stage
        export_action = pipeline_actions.CodeBuildAction(
            input=source_artifact,
            project=project,
            action_name="Export-interfaces-and-models"
        )
        export_stage = interface_pipeline.add_stage(
            stage_name="Export-interface-and-models")
        export_stage.add_action(
            export_action
        )

        # Trigger deployment pipeline
        trigger_project = build.Project(
            scope=self,
            id='trigger-codebuild',

            # badge=True,
            environment=build.BuildEnvironment(
                build_image=build.LinuxBuildImage.STANDARD_5_0,
                environment_variables={
                    "PIPELINE_NAME": build.BuildEnvironmentVariable(
                        value=deployment_pipeline.pipeline.pipeline_name,
                        type=build.BuildEnvironmentVariableType.PLAINTEXT)
                }
            ),
            build_spec=build.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "build": {
                            "commands": [
                                "echo \"Triggering pipeline on behalf of user after interface and model export.\"",
                                "aws codepipeline start-pipeline-execution --name ${PIPELINE_NAME}",
                                "echo \"Complete\""
                            ]
                        }
                    }
                }
            )
        )
        # Allow execution start
        trigger_project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["codepipeline:StartPipelineExecution"],
                resources=[deployment_pipeline.pipeline.pipeline_arn]
            )
        )

        # Add a trigger which triggers the deployment pipeline
        # corresponding to this stage

        # Run only after export interface finishes
        trigger_action = pipeline_actions.CodeBuildAction(
            input=source_artifact,
            project=trigger_project,
            action_name="Trigger-deployment-pipeline",
            run_order=2
        )
        export_stage.add_action(
            trigger_action
        )

        """
        ==============================
        UI BUILD ONLY UTILITY PIPELINE
        ==============================
        """
        ui_pipeline = code_pipeline.Pipeline(
            scope=self,
            id="ui-only-pipe",
            artifact_bucket=create_artifact_bucket(
                scope=self, id='uionly-artifacts'),
        )

        # Source repo
        source_artifact = code_pipeline.Artifact("source")
        ui_only_source_stage: code_pipeline.IStage = ui_pipeline.add_stage(
            stage_name="Source-repo")
        ui_only_source_stage.add_action(
            pipeline_actions.GitHubSourceAction(
                oauth_token=o_auth_token,
                output=source_artifact,
                owner=config.git_owner_org,
                repo=config.git_repo_name,
                branch=config.git_branch_name,
                trigger=pipeline_actions.GitHubTrigger.NONE,
                action_name="Source-repository"
            )
        )

        # deploy actions
        deploy_action_list = self.create_static_build_list_codebuild(
            source_artifact=source_artifact,
            shared_lib_env_variables=shared_lib_env_variables
        )

        ui_build_stage = ui_pipeline.add_stage(
            stage_name="Build-UIs")
        for action in deploy_action_list:
            ui_build_stage.add_action(action)

        """
        =========================
        PIPELINE ASSOCIATED INFRA
        =========================
        """

        # Get the underlying pipeline object and add notifications on all stages

        # Cannot edit this
        finalized_code_pipeline = deployment_pipeline.pipeline

        if config.email_alerts_activated:
            if not config.pipeline_alert_email:
                Annotations.of(self).add_error(
                    "Cannot have pipeline alerts without specifying email. Aborting.")
                raise ValueError()

            # Build filtered topic to email
            PipelineEventProcessor(
                scope=self,
                construct_id="pipeline-event-processor",
                code_pipeline=finalized_code_pipeline,
                email_address=config.pipeline_alert_email
            )

    def create_static_build_list(self, shared_lib_env_variables: Dict[str, str]) -> List[pipelines.ShellStep]:
        """    create_static_build_list
            Creates a list of shell steps for use in the pipeline.
            This is for building static websites.
            As you add static website builds, add to the list below.

            Returns
            -------
             : List[pipelines.ShellStep]
                The list of build steps to be added to pipeline.

            Raises
            ------
            Exception
                When you try to call without the deployment stage being in
                namespace will cause error.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        if (not self.deployment):
            raise Exception(
                "Called static build list before defining deployment stage.")

        build_steps = []

        data_store_env_base = {k: v for k,
                               v in shared_lib_env_variables.items()}
        data_store_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "data-store-ui"
            }
        )

        # Add the static UI page builds to pipeline as post step
        build_steps.append(
            generate_react_static_shell_step(
                id="data-store-ui",
                working_dir="data-store-ui",
                bucket_name_cfn_output=self.deployment.data_store_ui_bucket_name,
                standard_env_variables=data_store_env_base,
                other_environment_cfn_outputs={}
            )
        )

        registry_env_base = {k: v for k,
                             v in shared_lib_env_variables.items()}
        registry_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "entity-registry-ui"
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="registry-ui",
                working_dir="registry-ui",
                bucket_name_cfn_output=self.deployment.registry_ui_bucket_name,
                standard_env_variables=registry_env_base,
                other_environment_cfn_outputs={}
            )
        )

        prov_ui_env_base = {k: v for k,
                            v in shared_lib_env_variables.items()}
        prov_ui_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "provenance-store-ui"
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="prov-ui",
                working_dir="prov-ui",
                bucket_name_cfn_output=self.deployment.prov_ui_bucket_name,
                standard_env_variables=prov_ui_env_base,
                other_environment_cfn_outputs={
                }
            )
        )

        landing_portal_env_base = {k: v for k,
                                   v in shared_lib_env_variables.items()}
        landing_portal_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "landing-portal-ui",
            }
        )

        build_steps.append(
            generate_react_static_shell_step(
                id="landing-portal-ui",
                working_dir="landing-portal-ui",
                bucket_name_cfn_output=self.deployment.landing_page_ui_bucket_name,
                standard_env_variables=landing_portal_env_base,
                other_environment_cfn_outputs={}
            )
        )

        return build_steps

    def create_static_build_list_codebuild(self, source_artifact: code_pipeline.Artifact, shared_lib_env_variables: Dict[str, str]) -> List[pipeline_actions.CodeBuildAction]:
        """    create_static_build_list_codebuild
            This method is a helper function used to build code pipeline BuildAction friendly
            build actions. 
            The difference between this and the above action is that we are not in the 
            cdk.pipelines abstracted environment meaning we don't have access to the 
            nice management of CfnOutputs that cdk pipelines provides. So here, we can 
            use a similar interface, but need to define it ourselves, in this case 
            using the AWS CLI to describe the stack. 

            Arguments
            ----------
            source_artifact : code_pipeline.Artifact
                The github source object - required for producing the code build action.

            Returns
            -------
             : List[pipeline_actions.CodeBuildAction]
                The list of actions which can be added to a stage.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        build_steps = []

        data_store_env_base = {k: v for k,
                               v in shared_lib_env_variables.items()}
        data_store_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "data-store-ui"
            }
        )

        # Add the static UI page builds to pipeline as post step
        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-data-store",
                source_artifact=source_artifact,
                working_dir="data-store-ui",
                # Normal variables at deploy time
                standard_env_variables=data_store_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.data_store_ui_bucket_name,
                }
            )
        )

        registry_env_base = {k: v for k,
                             v in shared_lib_env_variables.items()}
        registry_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "entity-registry-ui"
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-registry",
                source_artifact=source_artifact,
                working_dir="registry-ui",
                # Normal variables at deploy time
                standard_env_variables=registry_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.registry_ui_bucket_name,
                }
            )
        )

        prov_ui_env_base = {k: v for k,
                            v in shared_lib_env_variables.items()}
        prov_ui_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "provenance-store-ui"
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-prov",
                source_artifact=source_artifact,
                working_dir="prov-ui",
                # Normal variables at deploy time
                standard_env_variables=prov_ui_env_base,
                # Special variables which are looked up for the specified
                # stack
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.prov_ui_bucket_name,
                }
            )
        )

        landing_portal_env_base = {k: v for k,
                                   v in shared_lib_env_variables.items()}
        landing_portal_env_base.update(
            {
                # TODO parameterise this
                "VITE_KEYCLOAK_CLIENT_ID": "landing-portal-ui",
            }
        )

        build_steps.append(
            generate_codebuild_static_action(
                scope=self,
                id="ui-only-landing-portal",
                source_artifact=source_artifact,
                working_dir="landing-portal-ui",
                standard_env_variables=landing_portal_env_base,
                cfn_output_name_key={
                    "BUCKET_NAME": self.deployment.landing_page_ui_bucket_name,
                }
            )
        )

        return build_steps
