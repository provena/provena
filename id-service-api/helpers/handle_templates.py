import string
from config import Config
from dependencies.dependencies import secret_cache
from pydantic import BaseModel
from helpers.keycloak_helpers import retrieve_secret_value
from fastapi import HTTPException
from cachetools.func import ttl_cache

"""
Contains the request template used to inject credentials into the POST request.
"""

PIDREQUEST = string.Template(u'''<?xml version="1.0" encoding="UTF-8"?>
<request name="${name}">
<properties>
    <property name="appId" value="${app_id}" />
    <property name="sharedSecret" value="${secret}" />
    <property name="identifier" value="${identifier}" />
    <property name="authDomain" value="${authdomain}" />
</properties>
</request>''')

R_TYPE = "mint"


class HandleCreds(BaseModel):
    appId: str
    sharedSecret: str
    identifier: str
    domain: str


@ttl_cache()
def get_handle_creds(creds_arn: str) -> HandleCreds:
    try:
        raw_output = retrieve_secret_value(
            secret_arn=creds_arn,
            secret_cache=secret_cache
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve credentials. Exception: {e}.")
    try:
        return HandleCreds.parse_raw(raw_output)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse credentials. Exception: {e}.")


def template_handle_request(config: Config) -> str:
    """
    template_handle_request 

    Uses the config creds to inject the creds into the templated XML body.

    Parameters
    ----------
    config : Config
        The config

    Returns
    -------
    str
        The injected string
    """
    creds = get_handle_creds(creds_arn=config.handle_service_creds_arn)
    return PIDREQUEST.safe_substitute(
        name=R_TYPE,
        app_id=creds.appId,
        secret=creds.sharedSecret,
        identifier=creds.identifier,
        authdomain=creds.domain
    )
