from enum import Enum
from tests.config import config
from SharedInterfaces.ProvenanceAPI import *
from KeycloakRestUtilities.Token import BearerAuth
import requests


class Direction(str, Enum):
    UPSTREAM = "UPSTREAM"
    DOWNSTREAM = "DOWNSTREAM"


def basic_prov_query(start: str, direction: Direction, depth: int, token: str) -> LineageResponse:
    prov_endpoint = config.PROV_API_ENDPOINT
    postfix = "/explore/" + direction.lower()
    endpoint = prov_endpoint + postfix
    params: Dict[str, str] = {
        'starting_id': start,
        'depth': str(depth)
    }
    response = requests.get(
        url=endpoint,
        params=params,
        auth=BearerAuth(token)
    )

    assert response.status_code == 200, f"Non 200 response code from prov query, code={response.status_code}, value={response.text}."
    return LineageResponse.parse_obj(response.json())


def successful_basic_prov_query(start: str, direction: Direction, depth: int, token: str) -> LineageResponse:
    res = basic_prov_query(
        start=start, direction=direction, depth=depth, token=token)
    assert res.status.success, f"Status failure in prov query. Info: {res.status.details or 'No details provided'}"

    return res
