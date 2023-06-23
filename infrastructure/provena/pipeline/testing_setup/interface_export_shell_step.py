from aws_cdk import (
    pipelines,
    aws_codebuild as build
)

from provena.pipeline.testing_setup.testing_config import INTERFACE_EXPORT_SCRIPT_LOCATION

def generate_interface_export_step(
    id: str
) -> pipelines.Step:
    return pipelines.CodeBuildStep(
        id=id,
        build_environment=build.BuildEnvironment(
            # Includes the ubuntu 20.04 chrome install for python etc
            build_image=build.LinuxBuildImage.from_code_build_image_id(
                "aws/codebuild/standard:5.0")
        ),
        commands=[
            f"./{INTERFACE_EXPORT_SCRIPT_LOCATION}"
        ]
    )
