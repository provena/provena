from time import sleep, time
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.RegistryAPI import *

from SharedInterfaces.ProvenanceModels import *
import requests
import json
from KeycloakRestUtilities.Token import BearerAuth
from requests import Response
from tests.config import config
from tests.helpers.registry_helpers import general_list_first_n

POLLING_TIMEOUT = 600 # 10 minutes

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
        config.PROV_API_ENDPOINT + '/model_run/register_complete',
        json=json.loads(model_run_record.json(exclude_none=True)),
        auth=BearerAuth(token)
    )

def assert_succesfull_create_model_run_and_parse(create_resp: Response) -> ProvenanceRecordInfo:
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
    assert create_resp.record_info, f"Recieved no record info to register model run."
    assert create_resp.record_info.record, "Recieved no record in record info to register model run."
    return create_resp.record_info

def register_modelrun_from_record_info_successfully(token: str, model_run_record: ModelRunRecord) -> ProvenanceRecordInfo:
    """Register a model run and assert that it was successful.

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
    create_resp = register_model_run_from_record_info(token=token, model_run_record=model_run_record)
    created_model_run_record = assert_succesfull_create_model_run_and_parse(create_resp=create_resp)
    return created_model_run_record


def register_modelrun_from_record_info_successfully_potential_timeout(token: str, model_run_record: ModelRunRecord, description_UUID: str) -> Tuple[str, ModelRunRecord]:
    """Register a model run and polls for succession to if a timeout response is recieved by trying to fetch
    the item. Useful when creating the very first model run (during integration tests) in the graph database and the id is required afterwards,
    perhaps for cleanup or other use. This is because DB initialisation causes a timeout.


    Parameters
    ----------
    token : str
        _description_
    model_run_record : ModelRunRecord
        The model run record to create.
    description_UUID : str
        The UUID of the description to be used in the model run record. This is used to identify the model run record
        we might need to search for via polling.

    Raises
    ------
    AssertionError
        If the polling times out.

    Returns
    -------
    Tuple[str, ModelRunRecord]
        The id and ModelRunRecord of the created model run
    """

    # create is done using the domain_info.record
    create_resp = register_model_run_from_record_info(token=token, model_run_record=model_run_record)
    created_record_info: Optional[ProvenanceRecordInfo]
    if create_resp.status_code != 504:
        # not a gateway time out, continue as normal
        created_record_info = assert_succesfull_create_model_run_and_parse(create_resp=create_resp)
        print("\nFetched Model Run without polling.")
        return (created_record_info.id, created_record_info.record) # id and ModelRunRecord
    else:
        # timed out, poll for success
        print("\nPolling to fetch Model Run.")
        s = time()
        found_model_run_tuple = None # will be non None when successful poll for desired model run to have been created
        while not found_model_run_tuple:
            found_model_run_tuple = timeout_creation_succeeded(token=token, description_UUID=description_UUID)
            sleep(5) # not necessary to poll every ms.
            assert time()-s < POLLING_TIMEOUT, f"Failed to find the created model run after {POLLING_TIMEOUT/60} minutes of polling!"
            
        print(f"\nFound the created model run after polling for {round(time()-s)} seconds.")
        return found_model_run_tuple # (model_run_id, ModelRunRecord)

def timeout_creation_succeeded(token: str, description_UUID: str) -> Optional[Tuple[str,ModelRunRecord]]:
    """Polls for the creation of a model run with the given description UUID.

    Parameters
    ----------
    token : str
        _description_
    description_UUID : str
        The UUID of the description to be used in the model run record. This is used to identify the model run record

    Returns
    -------
    Optional[Tuple[str,ModelRunRecord]]
        The id and ModelRunRecord of the created model run if found, otherwise None.
    """

    # Returns none if not succeed, otherwise returns the record info for the created model run.

    # returns the created model run record info if the desired to be creation record info is in the most recently created model runs.
    item_model_runs = list_n_latest_model_runs(token=token, n=3)
    for model_run_item in item_model_runs:
        if model_run_item.record.description and description_UUID in model_run_item.record.description:
            return (model_run_item.id, model_run_item.record)  # str, ModelRunRecord
    return None


def list_n_latest_model_runs(token: str, n: int) -> List[ItemModelRun]:
    """List the n most recent model runs.

    Parameters
    ----------
    token : str
        _description_
    n : int
        The number of model runs to list.

    Returns
    -------
    List[ItemModelRun]
        The list of model runs.
    """
    # fetch is done using the domain_info.record
    recent_model_runs_request = GeneralListRequest(
        filter_by=FilterOptions(
            item_subtype=ItemSubType.MODEL_RUN
        ),
        sort_by=SortOptions(
            sort_type=SortType.CREATED_TIME,
            ascending=False # most recent first
        ),
    )

    raw_model_runs = general_list_first_n(token=token, first_num=n, general_list_request=recent_model_runs_request)

    return [ItemModelRun.parse_obj(mr) for mr in raw_model_runs]