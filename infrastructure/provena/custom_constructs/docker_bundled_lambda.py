from aws_cdk import (
    BundlingOptions,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    Duration,
    BundlingOptions,
    ILocalBundling
)

from constructs import Construct
from typing import Optional, Dict, Any, List
import sys
import os
import jsii
from provena.utility.hash_dir import hash_dir

"""
==============================
LAMDBA DOCKER BUNDLING OPTIONS
==============================
"""
DEFAULT_DOCKER_LAMBDA_BUILD = True
DOCKER_QUIET = True

# Ignore pylint hint here -> This does exist!
# pylint: disable=no-member
LAMBDA_DOCKER_IMAGE = _lambda.Runtime.PYTHON_3_9.bundling_image
LAMBDA_REQUIREMENTS_FILE = "deploy_requirements.txt"
LOCAL_LAMBDA_REQUIREMENTS_FILE = "dev_requirements.txt"

# Set of commands which should be run inside the lambda bundle
DOCKER_COMMAND_LIST = [
    'mkdir -p /asset-output',
    'python3 -m pip install --no-cache --upgrade' + (' -q' if DOCKER_QUIET else '') +
    ' -r ' + LAMBDA_REQUIREMENTS_FILE + ' --target /asset-output',
    'cp -r ./* /asset-output',
    'touch /asset-output/__init__.py'
]

# requires knowing the output directory


def generate_local_commands(input: str, output: str) -> List[str]:
    return [
        f"cd {input} && pip install --no-cache --upgrade -r {LOCAL_LAMBDA_REQUIREMENTS_FILE} --target {output}",
        f"cp -r {input}/* {output}",
        f"touch {output}/__init__.py"
    ]


"""
===============
LAMBDA DEFAULTS
===============
"""

# Sets whether the lambda functions are built in a docker
# layer or if it is assumed that the libraries are manually
# packaged. The docker build requires a requirements.txt
# file alongside the lambda functions (even if it is empty).
DEFAULT_LAMBDA_NAME = "lambda_function"
DEFAULT_HANDLER_NAME = "main"
DEFAULT_HANDLER = DEFAULT_LAMBDA_NAME + "." + DEFAULT_HANDLER_NAME
DEFAULT_RUNTIME = _lambda.Runtime.PYTHON_3_9
LOW_MEMORY = 128  # MB

# Seems like this is the best choice of memory right now
MEDIUM_MEMORY = 768  # MB

PERFORMANCE_MEMORY = 1763  # MB

# Function default timeout
DEFAULT_LAMBDA_TIMEOUT = Duration.millis(20000)
"""
================
HELPER FUNCTIONS
================
"""


@jsii.implements(ILocalBundling)
class PythonLambdaBundler:
    def __init__(self, path: str) -> None:
        self.path = path

    def try_bundle(self, output_dir: str, options: Any) -> bool:
        # get the python version info
        major, minor, _, _, _ = sys.version_info

        if (major < 3) or (minor < 8):
            print("Local python version to old <3.8 to run local bundling.")
            return False

        # now check we have pip
        response = os.system('pip --version')
        if response != 0:
            print("Pip does not appear to exist in the python context.")
            return False

        # now run the bundling
        try:
            print(f"Performing local bundling on {self.path}...")
            local_command_list = generate_local_commands(
                input=self.path, output=output_dir)
            print("Command list:")
            print('\n'.join(local_command_list))
            for command in local_command_list:
                response = os.system(command)
                if response != 0:
                    raise Exception(
                        f"Command {command} had non zero return code! Aborting")
        except Exception as e:
            print(f"Failed local bundling with error {e}")
            return False

        return True


def create_lambda(scope: Construct,
                  id: str,
                  path: str,
                  handler: str,
                  timeout: Duration = DEFAULT_LAMBDA_TIMEOUT,
                  layers: List[Any] = [],
                  bundling_required: bool = DEFAULT_DOCKER_LAMBDA_BUILD,
                  runtime: _lambda.Runtime = DEFAULT_RUNTIME,
                  environment: Dict[str, str] = {},
                  concurrent_limit: Optional[int] = None,
                  dlq: Optional[sqs.IQueue] = None,
                  extra_hash_dirs: Optional[List[str]] = None,
                  memory: int = MEDIUM_MEMORY) -> _lambda.Function:
    """
    Returns a created lambda function with some basic default values
    and the required parameters filled in. If docker_build is
    switched on then a requirements.txt file must be in the directory.
    A docker build will be initiated with a python3.7 runtime, the requirements
    will be installed in the build then exported to the AWS build.
    """
    bundling_options = BundlingOptions(
        image=LAMBDA_DOCKER_IMAGE,
        command=[
            # create the asset directory, install requirements,
            # and move to output folder under libs directory
            'bash', '-c',
            '&&'.join(DOCKER_COMMAND_LIST)
        ],
        environment=environment,
        # Mypy doesn't understand this!
        local=PythonLambdaBundler(path)  # type: ignore
    )

    # if we are using custom hash dirs
    custom_hash: Optional[str] = None
    if extra_hash_dirs:
        full_hash_dirs: List[str] = [path] + extra_hash_dirs
        custom_hash = "".join([hash_dir(
            os.path.abspath(dir)
        ) for dir in full_hash_dirs])

    func = _lambda.Function(
        scope, id,
        runtime=runtime,
        timeout=timeout,
        handler=handler,
        layers=layers,
        code=_lambda.Code.from_asset(
            path=path,
            bundling=None if not bundling_required else bundling_options,
            asset_hash=custom_hash
        ),
        memory_size=memory,
        reserved_concurrent_executions=concurrent_limit,
        # turn on dlq if provided
        dead_letter_queue=dlq,
        dead_letter_queue_enabled=True if dlq else None,
    )

    return func


class DockerizedLambda(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 path: str,
                 handler: str,
                 timeout: Duration = DEFAULT_LAMBDA_TIMEOUT,
                 bundling_environment: Dict[str, str] = {},
                 lambda_environment: Dict[str, str] = {},
                 max_concurrency: Optional[int] = None,
                 dlq: Optional[sqs.IQueue] = None,
                 extra_hash_dirs: Optional[List[str]] = None,
                 ** kwargs: Any) -> None:

        # Super constructor
        super().__init__(scope, id, **kwargs)

        # Create the function
        self.function = create_lambda(
            scope=self,
            id=f"{id}_func",
            path=path,
            handler=handler,
            timeout=timeout,
            environment=bundling_environment,
            concurrent_limit=max_concurrency,
            dlq=dlq,
            extra_hash_dirs=extra_hash_dirs
        )

        for k, v in lambda_environment.items():
            self.function.add_environment(
                k, v
            )
