from aws_cdk import (
    CfnOutput,
    aws_codebuild as build
)
from dataclasses import dataclass
from typing import List, Dict, Callable
from provena.config.config_class import *


"""
=============
TYPE CHECKING
=============
"""

TS_TYPE_CHECKING_SCRIPT_LOCATION = "scripts/testing/typescript_type_checks.sh"
MYPY_TYPE_CHECKING_SCRIPT_LOCATION = "scripts/testing/mypy_type_checks.sh"
INTERFACE_EXPORT_SCRIPT_LOCATION = "scripts/interface_management/export_interfaces.sh"
MODEL_EXPORT_SCRIPT_LOCATION = "scripts/model_exporter/run_model_export.sh"
STATIC_BUILD_SCRIPT_LOCATION = "scripts/builds/static_react.sh"

"""
==========
UNIT TESTS
==========
"""

UNIT_TEST_SCRIPT = "scripts/testing/unit_tests.sh"

UNIT_TEST_COMMANDS = [
    f"./{UNIT_TEST_SCRIPT}"
]


def generate_unit_test_standard_env() -> Dict[str, str]:
    env: Dict[str, str] = {
    }
    return env


def generate_unit_secret_env_vars(config: UnitTestConfig, general_config: GeneralConfig) -> Dict[str, build.BuildEnvironmentVariable]:
    # handle authorisation
    handle_secret_arn = config.handle_secret_arn
    handle_endpoint = config.ardc_service_endpoint

    vars = {
        "HANDLE_SERVICE_ENDPOINT": build.BuildEnvironmentVariable(
            value=handle_endpoint,
            type=build.BuildEnvironmentVariableType.PLAINTEXT
        ),
        "HANDLE_SERVICE_CREDS_ARN": build.BuildEnvironmentVariable(
            value=handle_secret_arn,
            type=build.BuildEnvironmentVariableType.PLAINTEXT
        ),
        "DOCKERHUB_USERNAME": build.BuildEnvironmentVariable(
            value=f"{general_config.dockerhub_creds_arn}:username",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "DOCKERHUB_PASSWORD": build.BuildEnvironmentVariable(
            value=f"{general_config.dockerhub_creds_arn}:password",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
    }
    return vars


def generate_unit_test_cfn_env_vars() -> Dict[str, CfnOutput]:
    # No cfn outputs
    return {}


def generate_unit_test_install_commands() -> List[str]:
    # No install commands
    return []


"""
=================
INTEGRATION TESTS
=================
"""

INTEGRATION_TEST_SCRIPT = "scripts/testing/integration_tests.sh"

INTEGRATION_TEST_COMMANDS = [
    f"./{INTEGRATION_TEST_SCRIPT}"
]


def generate_integration_test_standard_env(config: IntegrationTestConfig) -> Dict[str, str]:
    env: Dict[str, str] = {
        # arbitrary bad handle
        "INVALID_HANDLE": "12345.1/5678",
        # client needs direct access grants and role scope for user/pass
        "KEYCLOAK_CLIENT_ID": config.keycloak_client_id
    }

    return env


def generate_integration_secret_env_vars(config: IntegrationTestConfig) -> Dict[str, build.BuildEnvironmentVariable]:
    # user credentials for integration test
    test_bots_creds_arn = config.integration_test_bots_creds_arn

    vars = {

        "SYSTEM_WRITE_USERNAME": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:username",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "SYSTEM_WRITE_PASSWORD": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:password",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "SYSTEM_WRITE_USERNAME_2": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:username2",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "SYSTEM_WRITE_PASSWORD_2": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:password2",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "ADMIN_USERNAME": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:admin_username",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "ADMIN_PASSWORD": build.BuildEnvironmentVariable(
            value=f"{test_bots_creds_arn}:admin_password",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
    }
    return vars


def generate_integration_test_cfn_env_vars(data_store_api_endpoint: CfnOutput, job_api_endpoint: CfnOutput, registry_api_endpoint: CfnOutput, keycloak_endpoint: CfnOutput, prov_api_endpoint: CfnOutput, auth_api_endpoint: CfnOutput) -> Dict[str, CfnOutput]:
    # Pass through of required cfn outputs to env
    env: Dict[str, CfnOutput] = {
        "DATA_STORE_API_ENDPOINT": data_store_api_endpoint,
        "KEYCLOAK_ENDPOINT": keycloak_endpoint,
        "REGISTRY_API_ENDPOINT": registry_api_endpoint,
        "PROV_API_ENDPOINT": prov_api_endpoint,
        "AUTH_API_ENDPOINT": auth_api_endpoint,
        "JOB_API_ENDPOINT" : job_api_endpoint,
    }

    return env


def generate_integration_test_install_commands() -> List[str]:
    # no install required
    return []


"""
============
SYSTEM TESTS
============
"""

SYSTEM_TEST_SCRIPT = "scripts/testing/system_tests.sh"

SYSTEM_TEST_COMMANDS = [
    f"./{SYSTEM_TEST_SCRIPT}"
]


def generate_system_test_standard_env(config: SystemTestConfig, data_store_url: str, landing_portal_url: str) -> Dict[str, str]:
    # System UI testing config - note the codebuild compat mode
    # The chrome path is injected at runtime as part of the script
    env = {
        "HEADLESS_MODE": "true",
        "COMPAT_CODEBUILD_MODE": "true",
        "DATA_STORE_URL": data_store_url,
        "LANDING_PORTAL_URL": landing_portal_url,
        "SHARED_LINK": config.shared_link
    }

    return env


def generate_system_secret_env_vars(config: SystemTestConfig) -> Dict[str, build.BuildEnvironmentVariable]:
    # user credentials
    creds_arn = config.user_creds_arn
    vars = {
        "TEST_USERNAME": build.BuildEnvironmentVariable(
            value=f"{creds_arn}:username",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
        "TEST_PASSWORD": build.BuildEnvironmentVariable(
            value=f"{creds_arn}:password",
            type=build.BuildEnvironmentVariableType.SECRETS_MANAGER
        ),
    }
    return vars


def generate_system_test_cfn_env_vars() -> Dict[str, CfnOutput]:
    # No cfn outputs required
    env: Dict[str, CfnOutput] = {
    }
    return env


def generate_system_test_install_commands() -> List[str]:
    # no install required
    return []
