from helpers.type_aliases import GetAuthFunction
from ProvenaInterfaces.RegistryModels import ItemModelRun, ItemBase, ItemSubType, MODEL_TYPE_MAP
from ProvenaInterfaces.RegistryAPI import SubtypeListRequest, PaginationKey, ModelRunListResponse
from ProvenaInterfaces.SharedTypes import StatusResponse
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import ROUTE_ACTION_CONFIG_MAP, RouteActions
from ProvenaSharedFunctionality.Registry.TestConfig import route_params, RouteParameters
from typing import Optional, List, Type
import requests
import json
from functools import lru_cache
from rich import print


def get_model_from_subtype(subtype: ItemSubType) -> Type[ItemBase]:
    for cat_sub, model in MODEL_TYPE_MAP.items():
        c, s = cat_sub
        if s == subtype:
            return model
    raise ValueError(f"Missing subtype {subtype} in model type map.")


@lru_cache
def get_item_subtype_route_params(item_subtype: ItemSubType) -> RouteParameters:
    """Given an item subtype, will source a its RouteParmeters
    Parameters
    ----------
    item_subtype : ItemSubType
        The desired Item subtype to source route parameters for
    Returns
    -------
    RouteParameters
        the routeparametrs for the desired item subtype
    """
    for item_route_params in route_params:
        if item_route_params.subtype == item_subtype:
            return item_route_params

    raise Exception(
        f"Was not able to source route parameters for desired item_subtype = {item_subtype}")


def get_route(action: RouteActions, params: RouteParameters) -> str:
    # check for special proxy types
    if params.use_special_proxy_modify_routes:
        if action == RouteActions.CREATE:
            action = RouteActions.PROXY_CREATE
        elif action == RouteActions.SEED:
            action = RouteActions.PROXY_SEED
        elif action == RouteActions.UPDATE:
            action = RouteActions.PROXY_UPDATE

    # get the route prefix
    prefix = f"/registry{params.route}"
    action_path = ROUTE_ACTION_CONFIG_MAP[action].path

    return prefix + action_path


@lru_cache
def get_route_from_subtype_action(subtype: ItemSubType, action: RouteActions) -> str:
    params = get_item_subtype_route_params(item_subtype=subtype)
    return get_route(action=action, params=params)


def response_success(response: requests.Response) -> None:
    if response.status_code != 200:
        raise Exception(f"Non 200 response code! Code: {response.status_code}")

    try:
        response_json = response.json()
    except Exception as e:
        raise Exception(f"Could not parse response as JSON: {e}")

    try:
        status_response = StatusResponse.parse_obj(response_json)
    except Exception as e:
        raise Exception(
            f"Could not parse JSON response as StatusResponse: {e}")

    if not status_response.status.success:
        raise Exception(f"Status success was False in StatusResponse")


@lru_cache
def fetch_from_registry_typed(
    endpoint: str,
    auth: GetAuthFunction,
    id: str,
    subtype: ItemSubType,
) -> ItemBase:
    print(f"Fetching {subtype} with id {id}")

    postfix = get_route_from_subtype_action(
        subtype=subtype, action=RouteActions.FETCH)
    full_endpoint = endpoint + postfix
    params = {
        'id': id
    }
    response = requests.get(url=full_endpoint, params=params, auth=auth())

    try:
        response_success(response)
    except Exception as e:
        raise Exception(f"Failed to fetch ID {id}, exception {e}.")

    model = get_model_from_subtype(subtype=subtype)
    try:
        return model.parse_obj(response.json()["item"])
    except Exception as e:
        raise Exception(
            f"Failed to parse fetched item with ID {id}, parse exception {e}.")


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
    postfix = "/registry/activity/model_run/list"
    full_endpoint = registry_endpoint + postfix

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
