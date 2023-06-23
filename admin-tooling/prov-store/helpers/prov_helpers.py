from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.RegistryAPI import *
import requests
from helpers.type_aliases import GetAuthFunction
import json
from rich import print


def relodge_model_run_record(
    record: ItemModelRun,
    auth: GetAuthFunction,
    validate_record: bool,
    prov_endpoint: str
) -> None:
    """
    relodge_model_run_record 

    Uses the prov store admin restore record endpoint to relodge the model run
    record into the graph store.

    Parameters
    ----------
    record : ItemModelRun
        The model run record
    stage : str
        The stage
    auth : GetAuthFunction
        The auth function
    validate_record : bool
        Should the prov store revalidate the record
    endpoint_override : Optional[str], optional
        Optionally override the stage endpoint, by default None
    """
    postfix = "/admin/store_record"
    full_endpoint = prov_endpoint + postfix
    body = json.loads(record.json())
    params = {
        'validate_record': validate_record
    }

    print(f"Pushing record id {record.id}...")
    # fetch the model run record
    response = requests.post(
        url=full_endpoint,
        json=body,
        params=params,
        auth=auth()
    )

    # check that the response was successful
    if response.status_code != 200:
        try:
            details = response.json()['detail']
        except:
            details = "Couldn't retrieve."
        raise Exception(
            f"Non 200 status code from prov API for record id {record.id}. Code: {response.status_code}. Details {details}.")

    # parse as status response
    status_response = StatusResponse.parse_obj(response.json())

    # check success
    assert status_response.status.success, f"Success was false on prov restore operation, details: {status_response.status.details}."
