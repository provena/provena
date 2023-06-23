import boto3  # type: ignore
import os

from typing import Dict, Any

# expect project ARN as env variable
codebuild_project_name = os.getenv("BUILD_PROJECT_NAME")
assert codebuild_project_name


def handler(event: Dict[str, Any], context: Any) -> None:
    # Print event for debugging if required
    print(event)

    # get a codebuild client and start project
    print("Setting up boto client")
    client = boto3.client('codebuild')

    # invoke
    print(f"Starting build for project: {codebuild_project_name}.")
    client.start_build(**{
        'projectName': codebuild_project_name,
    })

    print(f"Complete.")
