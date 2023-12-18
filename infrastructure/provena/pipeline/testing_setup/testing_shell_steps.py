from aws_cdk import (
    pipelines,
    aws_codebuild as build,
    aws_secretsmanager as sm,
)
from constructs import Construct

from provena.pipeline.testing_setup.testing_config import *


def generate_unit_tests(
    id: str,
    config: ProvenaConfig,
) -> pipelines.Step:
    """    generate_unit_tests
        Generates the unit test step

        Arguments
        ----------
        id : str
            The id of the step to create (shown on pipeline)
        stage : str
            The stage

        Returns
        -------
         : pipelines.ShellStep
            The shell step output

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # unit_test : TestConfiguration <- testing_config

    # standard env
    standard_env = generate_unit_test_standard_env()

    # convert standard envs to build environment vars
    build_vars = {key: build.BuildEnvironmentVariable(
        value=value, type=build.BuildEnvironmentVariableType.PLAINTEXT) for key, value in standard_env.items()}

    # Cfn env
    assert config.tests.unit_tests, "Need unit test config"

    cfn_env = generate_unit_test_cfn_env_vars(
    )

    # secret env
    secret_env = generate_unit_secret_env_vars(
        config=config.tests.unit_tests,
        general_config=config.general
    )

    # combine secret and plaintext env variables
    combined_env = {k: v for k, v in list(
        secret_env.items()) + list(build_vars.items())}

    # install commands
    install_commands = generate_unit_test_install_commands()

    # use custom codebuild step to enable secret injection
    step = pipelines.CodeBuildStep(
        id=id,
        commands=UNIT_TEST_COMMANDS,
        env_from_cfn_outputs=cfn_env,
        build_environment=build.BuildEnvironment(
            environment_variables=combined_env,
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:7.0"),
            privileged=True
        ),
        install_commands=install_commands
    )

    return step


def generate_integration_tests(
    id: str,
    config: ProvenaConfig,
    data_store_api_endpoint: CfnOutput,
    job_api_endpoint: CfnOutput,
    registry_api_endpoint: CfnOutput,
    keycloak_endpoint: CfnOutput,
    prov_api_endpoint: CfnOutput,
    auth_api_endpoint: CfnOutput,
) -> pipelines.Step:
    """    generate_integration_tests
        Generate integration tests Step

        Arguments
        ----------
        id : str
            The id of the step shown in pipeline console
        stage : str
            The stage
        data_store_api_endpoint : CfnOutput
            API Endpoint cfn output from deployment infra
        keycloak_endpoint : CfnOutput
            Keycloak endpoint cfn output (/realms/realm_name)

        Returns
        -------
         : Step
            Pipeline step

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # integration_test : TestConfiguration <- testing_config

    # standard env
    assert config.tests.integration_tests
    standard_env = generate_integration_test_standard_env(
        config=config.tests.integration_tests
    )

    # convert standard envs to build environment vars
    build_vars = {key: build.BuildEnvironmentVariable(
        value=value, type=build.BuildEnvironmentVariableType.PLAINTEXT) for key, value in standard_env.items()}

    # Cfn env
    cfn_env = generate_integration_test_cfn_env_vars(
        data_store_api_endpoint=data_store_api_endpoint,
        registry_api_endpoint=registry_api_endpoint,
        keycloak_endpoint=keycloak_endpoint,
        prov_api_endpoint=prov_api_endpoint,
        auth_api_endpoint=auth_api_endpoint,
        job_api_endpoint=job_api_endpoint
    )

    # secret env
    secret_env = generate_integration_secret_env_vars(
        config=config.tests.integration_tests)

    # combine secret and plaintext env variables
    combined_env = {k: v for k, v in list(
        secret_env.items()) + list(build_vars.items())}

    # install commands
    install_commands = generate_integration_test_install_commands()

    # Build codebuildstep to enable secret injection
    step = pipelines.CodeBuildStep(
        id=id,
        commands=INTEGRATION_TEST_COMMANDS,
        env_from_cfn_outputs=cfn_env,
        build_environment=build.BuildEnvironment(
            environment_variables=combined_env,
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:7.0")
        ),
        install_commands=install_commands
    )

    return step


def generate_system_tests(
    id: str,
    config: ProvenaConfig,
    data_store_url: str,
    landing_portal_url: str
) -> pipelines.Step:
    """    generate_system_tests
        Generate system test pipeline step

        Arguments
        ----------
        id : str
            The id to show in pipeline console
        stage : str
            The deployment stage
        data_store_url : str
            Data store URL to test
        landing_portal_url : str
            Landing portal URL to test

        Returns
        -------
         : pipelines.Step
            The pipelines step output

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # system_test : TestConfiguration <- testing_config

    assert config.tests.system_tests

    # standard env
    standard_env = generate_system_test_standard_env(
        config=config.tests.system_tests,
        data_store_url=data_store_url,
        landing_portal_url=landing_portal_url
    )

    # convert standard envs to build environment vars
    build_vars = {key: build.BuildEnvironmentVariable(
        value=value, type=build.BuildEnvironmentVariableType.PLAINTEXT) for key, value in standard_env.items()}

    # Cfn env
    cfn_env = generate_system_test_cfn_env_vars(
    )

    # secret env
    secret_env = generate_system_secret_env_vars(
        config=config.tests.system_tests)

    # combine secret and plaintext env variables
    combined_env = {k: v for k, v in list(
        secret_env.items()) + list(build_vars.items())}

    # install commands
    install_commands = generate_system_test_install_commands()

    step = pipelines.CodeBuildStep(
        id=id,
        commands=SYSTEM_TEST_COMMANDS,
        build_environment=build.BuildEnvironment(
            environment_variables=combined_env,
            # Includes the ubuntu 20.04 chrome install for system tests
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:7.0")
        ),
        env_from_cfn_outputs=cfn_env,
        install_commands=install_commands
    )

    return step
