import boto3  # type: ignore
import os
import base64
import traceback
from hashlib import sha256
from datetime import datetime, timezone
import json
from typing import Dict, Any

# response type alias
LambdaResponse = Dict[str, Any]

# Acknowledgements to https://github.com/mmuller88/aws-cdk-build-badge/blob/master/src/index.badge.ts
# for the idea

PIPELINE_NAME = os.getenv("PIPELINE_NAME")
assert PIPELINE_NAME

BADGE_DIR = "badges"

BADGE_MAP = {
    "InProgress": "in_progress.svg",
    "Succeeded": "succeeded.svg",
    "Superseded": "stopped.svg",
    "Failed": "failed.svg",
    "Cancelled": "stopped.svg",
    "Stopped": "stopped.svg",
    "Stopping": "in_progress.svg",
    "NotFound": "not_found.svg"
}

HEADERS = {
    'Content-Type': 'image/svg+xml',
    'Cache-Control': 'no-cache'
}


def pretty_time_delta(seconds: int) -> str:
    # from https://gist.github.com/thatalextaylor/7408395
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd%dh' % (days, hours)
    elif hours > 0:
        return '%dh%dm' % (hours, minutes)
    elif minutes > 0:
        return '%dm%ds' % (minutes, seconds)
    else:
        return '%dm%ds' % (0, seconds)


def generate_etag(hash_string: str) -> str:
    """    generate_etag
        Given the execution item will pull the execution ID 
        and perform a SHA256 hex digest to generate a unique cache
        eTag to avoid github caching the image.

        Arguments
        ----------
        hash_string : str 
            The string to hash

        Returns
        -------
         : str
            The hex hash digest

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return sha256(hash_string.encode()).hexdigest()


for k, v in BADGE_MAP.items():
    BADGE_MAP[k] = f"{BADGE_DIR}/{v}"


def generate_badge() -> LambdaResponse:
    try:
        # Create client
        client = boto3.client('codepipeline')

        # list executions
        print("Listing executions")
        response = client.list_pipeline_executions(
            pipelineName=PIPELINE_NAME
        )

        # Parse
        execs = response['pipelineExecutionSummaries']

        assert len(execs) > 0

        # get latest and status
        print("Found item - parsing status.")
        latest = execs[0]
        status = latest['status']

        # map to badge
        print("Choosing badge")
        badge_file_loc = BADGE_MAP[status]
        assert badge_file_loc

        # working out passed time
        passed: str = pretty_time_delta((datetime.now(
            latest['lastUpdateTime'].tzinfo) - latest['lastUpdateTime']).total_seconds())

        # based on https://stackoverflow.com/questions/3715493/encoding-an-image-file-with-base64
        with open(badge_file_loc, "r") as image_contents:
            contents = image_contents.read()

        # Replace all mentions of duration
        updated = contents.replace("DURATION", passed)

        # Base 64 encoding
        print("Producing b64 encoding")
        base64_content = base64.b64encode(updated.encode())

        print("Returning image data")

        # Generate Etag header item
        HEADERS['ETag'] = generate_etag(str(latest['lastUpdateTime']))
        HEADERS['Content-Type'] = 'image/svg+xml'
        # produce file response
        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': base64_content,
            'isBase64Encoded': True
        }
    except Exception as e:
        # if anything goes wrong, return not found

        # print exception to log
        print(f"Attempting to return not found badge.")
        print(f"Exception occurred:")
        traceback.print_exc()

        # Construct a fake hash of current date to keep it invalidated
        HEADERS['ETag'] = generate_etag(str(datetime.now()))
        HEADERS['Content-Type'] = 'image/svg+xml'

        badge_file_loc = BADGE_MAP["NotFound"]
        with open(badge_file_loc, "rb") as image_contents:
            base64_content = base64.b64encode(image_contents.read())
        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': base64_content,
            'isBase64Encoded': True
        }


def last_build() -> LambdaResponse:
    try:
        # Create client
        client = boto3.client('codepipeline')

        # list executions
        print("Listing executions")
        response = client.list_pipeline_executions(
            pipelineName=PIPELINE_NAME
        )

        # Parse
        execs = response['pipelineExecutionSummaries']

        assert len(execs) > 0

        # get latest and status
        print("Found item - parsing status.")
        latest = execs[0]

        # Generate Etag header item
        HEADERS['ETag'] = generate_etag(str(datetime.now()))
        HEADERS['Content-Type'] = "text/plain"

        # produce file response
        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': pretty_time_delta((datetime.now(latest['lastUpdateTime'].tzinfo) - latest['lastUpdateTime']).total_seconds()),
            'isBase64Encoded': False
        }

    except Exception as e:
        # if anything goes wrong, return error

        # print exception to log
        print(f"Something went wrong retrieving time")
        print(f"Exception occurred:")
        traceback.print_exc()

        # Construct a fake hash of current date to keep it invalidated
        HEADERS['ETag'] = generate_etag(str(datetime.now()))
        HEADERS['Content-Type'] = "text/plain"

        return {
            'statusCode': 500,
            'headers': HEADERS,
            'body': 'Unknown - error',
            'isBase64Encoded': False
        }


def handler(event: Dict[str, Any], context: Any) -> LambdaResponse:
    print("Processing request for build badge.")
    print("Building code pipeline client")

    methods = {
        ("GET", "/"): generate_badge
    }

    # parse method info
    method = event['httpMethod']
    path = event['path']

    # Check if there is a handler
    if (method, path) in methods.keys():
        # If there is, then call that method
        handler = methods[(method, path)]
        return handler()
    else:
        # otherwise respond with an error
        return {
            "statusCode": 405,
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({"data": "Error",
                                "message": f"Invalid method/path {method}:{path}"})
        }
