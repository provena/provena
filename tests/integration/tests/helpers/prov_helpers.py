from time import sleep, time
from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.AsyncJobModels import JobStatusTable, ProvLodgeModelRunResult, JobStatus
from ProvenaInterfaces.ProvenanceModels import *
import requests
import json
from KeycloakRestUtilities.Token import BearerAuth
from requests import Response
from tests.config import config, TokenGenerator, Config
from tests.helpers.registry_helpers import general_list_first_n
from tests.helpers.async_job_helpers import wait_for_full_lifecycle
from dataclasses import dataclass
import networkx as nx  # type: ignore
from typing import cast


def register_model_run_from_record_info(token: str, model_run_record: ModelRunRecord) -> Response:
    """Register a model run from a model run record.

    Parameters
    ----------
    token : str
        _description_
    model_run_record : ModelRunRecord
        The model run record to create.

    Returns
    -------
    Response
        The response from the server.
    """
    # create is done using the domain_info.record
    return requests.post(
        config.PROV_API_ENDPOINT + '/model_run/register',
        json=json.loads(model_run_record.json(exclude_none=True)),
        auth=BearerAuth(token)
    )


def assert_succesfull_lodge_model_run_and_parse(create_resp: Response) -> RegisterModelRunResponse:
    """Assert that the model run was created successfully and parse the response.

    Parameters
    ----------
    create_resp : Response
        The response from the server.

    Returns
    -------
    ProvenanceRecordInfo
        The record info of the created model run
    """
    assert create_resp.status_code == 200, f"Recieved non 200 status code ({create_resp.status_code}) to register model run. Details: {create_resp.json()}"
    create_resp = RegisterModelRunResponse.parse_obj(create_resp.json())
    assert create_resp.status.success, f"Recieved failed status to register model run. {create_resp.status.details}"
    return create_resp


def assert_succesfull_create_model_run_and_parse(status: JobStatusTable) -> ProvenanceRecordInfo:
    """Assert that the model run was created successfully and parse the response.

    Parameters
    ----------
    create_resp : Response
        The response from the server.

    Returns
    -------
    ProvenanceRecordInfo
        The record info of the created model run
    """
    assert status.status == JobStatus.SUCCEEDED, f"Expected successful prov lodge but had status {status.status}. Info: {status.info or 'None provided'}"

    # parse the result payload from job status
    result = ProvLodgeModelRunResult.parse_obj(status.result)

    assert result.record.record, "Recieved no record in record info to register model run."
    return result.record


def register_modelrun_from_record_info_successfully(get_token: TokenGenerator, model_run_record: ModelRunRecord) -> ProvenanceRecordInfo:
    """Register a model run and assert that it was successful.

    Will wait for job infra to dispatch and finish job. 

    Blocking operation.

    Parameters
    ----------
    token : str
        _description_
    model_run_record : ModelRunRecord
        The model run record to create.

    Returns
    -------
    ProvenanceRecordInfo
        The record info of the created model run
    """

    # create is done using the domain_info.record
    create_resp = register_model_run_from_record_info(
        token=get_token(), model_run_record=model_run_record)

    lodge_resp = assert_succesfull_lodge_model_run_and_parse(
        create_resp=create_resp)

    session_id = lodge_resp.session_id
    assert session_id

    payload = wait_for_full_lifecycle(
        session_id=session_id, get_token=get_token)

    created_model_run_record = assert_succesfull_create_model_run_and_parse(
        status=payload)
    return created_model_run_record


def register_modelrun_from_record_info_failed(get_token: TokenGenerator, model_run_record: ModelRunRecord, expected_code: int) -> Tuple[bool, Optional[ProvenanceRecordInfo]]:
    """Register a model run and assert that it failed.

    Expects failure of initial stage.

    Parameters
    ----------
    token : str
        _description_
    model_run_record : ModelRunRecord
        The model run record to create.

    Returns
    -------
    bool, Optional[ProvenanceRecordInfo]
        True, None iff expected Code
        False, details if the registration didn't fail - allows cleanup anyway
    """

    # create is done using the domain_info.record
    create_resp = register_model_run_from_record_info(
        token=get_token(), model_run_record=model_run_record)

    if create_resp.status_code == 200:
        lodge_resp = assert_succesfull_lodge_model_run_and_parse(
            create_resp=create_resp)

        session_id = lodge_resp.session_id
        assert session_id

        payload = wait_for_full_lifecycle(
            session_id=session_id, get_token=get_token)

        created_model_run_record = assert_succesfull_create_model_run_and_parse(
            status=payload)

        return False, created_model_run_record
    elif create_resp.status_code == expected_code:
        return True, None
    else:
        assert False, f"Status code was expected to be {expected_code} but was {create_resp.status_code}. Details: {create_resp.text}."


Graph = Dict[str, Any]


@dataclass
class GraphProperty():
    type: str
    source: str
    target: str


def assert_graph_property(prop: GraphProperty, graph: Graph) -> None:
    """

    Determines if the desired graph property exists in the networkX JSON graph
    in the graph object.

    Uses assertions to raise an assertion error if the property is not present.

    Args:
        prop (GraphProperty): The desired property 

        graph (Graph): The graph to analyse
    """

    links = graph['links']
    found = False
    for l in links:
        actual_prop = GraphProperty(**l)
        if actual_prop == prop:
            found = True
            break

    assert found, f"Could not find relation specified {prop}."


def assert_non_empty_graph_property(prop: GraphProperty, lineage_response: LineageResponse) -> None:
    """
    Determines if the desired graph property exists in the networkX JSON graph
    lineage response in the graph object.

    Uses assertions to raise an assertion error if the property is not present.

    Args:
        prop (GraphProperty): The desired property 

        graph (Graph): The graph to analyse
    """
    g = lineage_response.graph
    assert g is not None, f"Empty graph when non empty graph was expected."
    assert_graph_property(prop=prop, graph=g)
