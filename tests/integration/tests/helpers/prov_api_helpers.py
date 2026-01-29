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


def generate_report(token: str, node_id: str, upstream_depth: int, item_subtype: ItemSubType) -> Response:
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

    return response


def generate_report_and_wait_successfully(get_token: TokenGenerator, node_id: str, upstream_depth: int, item_subtype: ItemSubType) -> ByteString:
    """Lodge a generate-report job, wait for it to complete successfully, then download and return the report bytes.

    Parameters
    ----------
    get_token : TokenGenerator
        Callable that returns an auth token string when invoked.
    node_id : str
        The id to generate the report from.
    upstream_depth : int
        Upstream depth for traversal.
    item_subtype : ItemSubType
        The subtype of the node (STUDY or MODEL_RUN).

    Returns
    -------
    ByteString
        The downloaded report bytes.
    """

    response = generate_report(
        token=get_token(),
        node_id=node_id,
        upstream_depth=upstream_depth,
        item_subtype=item_subtype
    )

    assert response.status_code == 200, f"Expected a status code of 200 when lodging job, received {response.status_code}"

    payload_json = response.json()
    session_id = payload_json.get("session_id") or payload_json.get("sessionId")
    assert session_id is not None, "Generate report response did not include a session_id"

    job_status = wait_for_full_lifecycle(session_id=session_id, get_token=get_token)

    assert job_status.result is not None, "Job succeeded but did not include a result payload"
    report_url = job_status.result.get("report_url") or job_status.result.get("reportUrl")
    assert report_url is not None, "Job result did not include a report URL"

    download_resp = requests.get(report_url)
    assert download_resp.status_code == 200, f"Failed to download report from presigned URL, status {download_resp.status_code}"
    assert download_resp.content is not None and len(download_resp.content) > 0, "Downloaded report content was empty"

    return download_resp.content
