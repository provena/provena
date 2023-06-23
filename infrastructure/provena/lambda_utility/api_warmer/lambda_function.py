import boto3  # type: ignore
import json
import os
import requests
import logging
from typing import Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


from typing import Dict, Any

# API endpoints to hit
API_ENDPOINTS = [
    "DATA_STORE_API_ENDPOINT",
    "REGISTRY_API_ENDPOINT",
    "PROV_API_ENDPOINT",
    "HANDLE_API_ENDPOINT",
    "AUTH_API_ENDPOINT",
    "SEARCH_API_ENDPOINT"
]


def get_endpoint(env_name: str) -> Optional[str]:
    possible = os.getenv(env_name)
    if possible is None:
        logger.error(
            f"Could not find the endpoint with environment name: {env_name}.")
        return None
    return possible


resolved_endpoints = list(
    filter(lambda x: x is not None, map(get_endpoint, API_ENDPOINTS)))


def handler(event: Dict[str, Any], context: Any) -> None:
    # Print event for debugging if required
    logger.debug(event)

    success = []
    error = []

    # send API requests
    for endpoint in resolved_endpoints:
        try:
            response = requests.get(endpoint)
        except Exception as e:
            logger.error(
                f"Experienced exception: {e}. When trying to fetch against {endpoint}.")
            error.append(endpoint)
            continue

        if response.status_code != 200:
            logger.error(
                f"Failed to make a get request against {endpoint}. Status code: {response.status_code}.")
            error.append(endpoint)
        else:
            logger.info(
                f"Successful request to {endpoint}."
            )
            success.append(endpoint)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps({
            "success": success,
            "error": error
        })
    }
