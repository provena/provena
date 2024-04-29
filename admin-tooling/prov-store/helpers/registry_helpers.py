from ProvenaInterfaces.RegistryAPI import *
import requests
from helpers.type_aliases import GetAuthFunction
from rich import print
import json


def get_model_run_by_handle(
    handle_id: str,
    auth: GetAuthFunction,
    registry_endpoint: str,
) -> ItemModelRun:
    """
    get_model_run_by_handle

    Given the handle, stage and auth, will pull the given handle's model run
    record

    Parameters
    ----------
    handle_id : str
        The handle of the model run record
    stage : str
        The application stage
    auth : GetAuthFunction
        The auth function

    Returns
    -------
    ItemModelRun
        The complete ItemModelRun, or an error raised
    """
    base = registry_endpoint
    postfix = "/registry/activity/model_run/fetch"
    full_endpoint = base + postfix
    params = {
        'id': handle_id
    }

    # fetch the model run record
    print(f"Fetching record id {handle_id} ...")
    response = requests.get(
        url=full_endpoint,
        params=params,
        auth=auth()
    )

    # check that the response was successful
    assert response.status_code == 200, f"Non 200 status code from registry for handle {handle_id}. Code: {response.status_code}."

    # parse as model run response
    model_run_response = ModelRunFetchResponse.parse_obj(response.json())

    # check success
    assert model_run_response.status.success, f"Success is false on model run fetch response, details: {model_run_response.status.details}."

    # check the object exists
    assert model_run_response.item, f"Item was none despite successful response!"

    # check it is not a seed item
    assert model_run_response.item.record_type == RecordType.COMPLETE_ITEM, f"Item was not complete! Cannot restore into neo4j."

    # All good
    assert isinstance(model_run_response.item, ItemModelRun)
    return model_run_response.item


def list_model_run_records_from_registry(
    auth: GetAuthFunction,
    registry_endpoint: str
) -> List[ItemModelRun]:
    """
    list_model_run_records_from_registry 

    Retrieves a complete list of all model run records in the registry for
    relodging.

    Parameters
    ----------
    stage : str
        The stage to target
    auth : GetAuthFunction
        The auth function
    registry_endpoint_override : Optional[str], optional
        Optional override of registry endpoint, by default None

    Returns
    -------
    List[ItemModelRun]
        The list of complete item model runs

    Raises
    ------
    Various exceptions for failure conditions



    """
    base = registry_endpoint
    postfix = "/registry/activity/model_run/list"
    full_endpoint = base + postfix

    list_request = SubtypeListRequest()

    pagination_key: Optional[PaginationKey] = None

    complete_items: List[ItemModelRun] = []
    exhausted = False

    while not exhausted:
        list_request.pagination_key = pagination_key
        fetch_response = requests.post(
            url=full_endpoint, json=json.loads(list_request.json()), auth=auth())

        # check the status of the response
        status_code = fetch_response.status_code
        if status_code != 200:
            # try and get details then raise HTTPException
            try:
                detail = fetch_response.json()['detail']
                raise Exception(
                    f"Registry API responded with non 200 code: {status_code}. Error: {detail}")
            except:  # unable to get details
                raise Exception(
                    f"Registry API responded with non 200 code: {status_code}. ")

        # 200 code meaning that parse model will be valid
        try:
            model_run_list_response: ModelRunListResponse = ModelRunListResponse.parse_obj(
                fetch_response.json())
        except Exception as e:
            raise Exception(
                f"Tried to parse successful response from registry API model run list endpoint but failed. Parse error {e}.")

        # We now have a parsed model response
        if model_run_list_response.status.success:
            if model_run_list_response.items:
                complete_items.extend([ItemModelRun.parse_obj(i)
                                      for i in model_run_list_response.items])
            else:
                raise Exception(
                    "Response from registry API was successful but had no item property!"
                )
        else:
            raise Exception(
                f"Response from registry API was unsuccessful, error: {model_run_list_response.status.details}."
            )

        pagination_key = model_run_list_response.pagination_key
        if pagination_key is None:
            exhausted = True

    return complete_items
