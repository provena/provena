from aws_cdk import (
    pipelines,
    aws_codebuild as build
)

from provena.pipeline.testing_setup.testing_config import TS_TYPE_CHECKING_SCRIPT_LOCATION, MYPY_TYPE_CHECKING_SCRIPT_LOCATION

def generate_typescript_checking_step(
    id: str
) -> pipelines.Step:
    return pipelines.CodeBuildStep(
        id=id,
        build_environment=build.BuildEnvironment(
            # Includes the ubuntu 20.04 chrome install for npm etc
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:7.0")
        ),
        commands = [
            f"./{TS_TYPE_CHECKING_SCRIPT_LOCATION}"
        ]
    )

def generate_mypy_checking_step(
    id: str
) -> pipelines.Step:
    return pipelines.CodeBuildStep(
        id=id,
        build_environment=build.BuildEnvironment(
            # Includes the ubuntu 20.04 chrome install for npm etc
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:7.0")
        ),
        commands = [
            f"./{MYPY_TYPE_CHECKING_SCRIPT_LOCATION}"
        ]
    )