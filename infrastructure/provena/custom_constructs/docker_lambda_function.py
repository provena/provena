from aws_cdk import (
    aws_lambda as _lambda,
    Duration,
)

from constructs import Construct
from typing import Optional, Dict, Any, List
import checksumdir
import os
from provena.utility import hash_dir

"""
===============
LAMBDA DEFAULTS
===============
"""

LOW_MEMORY = 128  # MB

# Seems like this is the best choice of memory right now
MEDIUM_MEMORY = 768  # MB

PERFORMANCE_MEMORY = 1763  # MB

# Adjust
DEFAULT_MEMORY_SIZE = MEDIUM_MEMORY

# Function default timeout
DEFAULT_LAMBDA_TIMEOUT = Duration.millis(20000)
"""
================
HELPER FUNCTIONS
================
"""


class DockerImageLambda(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 build_directory: str,
                 dockerfile_path_relative: str,
                 extra_hash_dirs: List[str] = [],
                 build_args: Optional[Dict[str, str]] = {},
                 timeout: Optional[Duration] = DEFAULT_LAMBDA_TIMEOUT,
                 memory_size: Optional[int] = DEFAULT_MEMORY_SIZE,
                 **kwargs: Any) -> None:

        # Super constructor
        super().__init__(scope, id, **kwargs)

        extra_hash: Optional[str] = None
        if len(extra_hash_dirs) > 0:
            extra_hash = " ".join([hash_dir.hash_dir(
                os.path.abspath(dir)
            ) for dir in extra_hash_dirs])

        final_build_args: Dict[str, str] = {}

        # add cache buster == MD5 hash of extra things to force Docker to rebuild images
        if extra_hash:
            final_build_args['CACHE_BUSTER'] = extra_hash

        if build_args:
            final_build_args.update(build_args)

        # Create function
        self.function = _lambda.DockerImageFunction(
            self,
            'function',
            code=_lambda.DockerImageCode.from_image_asset(
                directory=build_directory,
                build_args=final_build_args,
                file=dockerfile_path_relative,
                extra_hash=extra_hash
            ),
            timeout=timeout,
            memory_size=memory_size,
        )
