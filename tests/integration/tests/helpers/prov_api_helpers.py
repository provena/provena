from enum import Enum
from tests.config import TokenGenerator, config
from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.AsyncJobModels import JobStatus
from KeycloakRestUtilities.Token import BearerAuth
import requests
from requests import Response
from typing import ByteString

from tests.helpers.async_job_helpers import wait_for_full_lifecycle


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


def link_model_run_to_study_successfully(token: TokenGenerator, study_id: str, model_run_id: str) -> AddStudyLinkResponse:
    """Link a model run to a study and wait for the job to complete, and assert success.

    Parameters
    ----------
    token : TokenGenerator
        _description_
    study_id : str
        The study ID to link to.
    model_run_id : str
        The model run ID to link.

    Returns
    -------
    AddStudyLinkResponse
        Study link response parsed model
    """
    res: Response = link_model_run_to_study(token=token(), study_id=study_id, model_run_id=model_run_id)
    assert res.status_code == 200, f"Non 200 response code from linking model run to study, code={res.status_code}, value={res.text}."
    res = AddStudyLinkResponse.parse_obj(res.json())
    assert res.status.success, f"Status failure in linking model run to study. Info: {res.status.details or 'No details provided'}"
    
    payload = wait_for_full_lifecycle(
        session_id=res.session_id, get_token=token)
    assert payload.status == JobStatus.SUCCEEDED, f"Failed to link model run to study. Status: {payload.status}"
    return res

def link_model_run_to_study(token: str, study_id: str, model_run_id: str) -> Response:
    """Link a model run to a study.

    Parameters
    ----------
    token : str
        _description_
    study_id : str
        The study ID to link to.
    model_run_id : str
        The model run ID to link.

    Returns
    -------
    Response
        raw response from the server.
    """
    return requests.post(
        config.PROV_API_ENDPOINT + '/model_run/edit/link_to_study',
        params={
            'study_id': study_id,
            'model_run_id': model_run_id
        },
        auth=BearerAuth(token)
    )

def generate_report_successfully(token: str, node_id: str, upstream_depth: int, item_subtype: ItemSubType) -> ByteString:
    """Helper function that calls the generate report endpoint.

    Parameters
    ----------
    token : str
        Auth token used to make API request.
    node_id : str
        ID of the respective node that the PROV-GRAPH report generation
        will commence from. (Can be of TYPE STUDY OR MODEL_RUN)
    upstream_depth : int
        The upstream depth to traverse to.
    item_subtype : ItemSubType
        The category of the respective node (Can be of type of STUDY OR MODEL_RUN)

    Returns
    -------
    Response
        A raw response object returned server.
    """

    base_endpoint = config.PROV_API_ENDPOINT + '/explore'
    complete_endpoint = base_endpoint + '/generate/report'
    json_body = {
        "id": node_id, 
        "depth": upstream_depth,
        "item_subtype": item_subtype
    }

    response: Response = requests.post(
        url=complete_endpoint,
        json=json_body,
        auth=BearerAuth(token)
    )

    assert response.content

    return response.content



