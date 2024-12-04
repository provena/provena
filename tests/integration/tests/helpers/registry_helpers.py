from requests import Response
from tests.helpers.general_helpers import display_failed_cleanups
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import ROUTE_ACTION_CONFIG_MAP, RouteActions
from ProvenaInterfaces.TestConfig import RouteParameters, route_params, non_test_route_params
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
import requests
import json
from KeycloakRestUtilities.Token import BearerAuth
from tests.config import config
from tests.helpers.general_helpers import py_to_dict
from typing import cast


def get_route(action: RouteActions, params: RouteParameters) -> str:
    # check for special proxy types
    if params.use_special_proxy_modify_routes:
        if action == RouteActions.CREATE:
            action = RouteActions.PROXY_CREATE
        elif action == RouteActions.SEED:
            action = RouteActions.PROXY_SEED
        elif action == RouteActions.UPDATE:
            action = RouteActions.PROXY_UPDATE
        elif action == RouteActions.REVERT:
            action = RouteActions.PROXY_REVERT

    # get the route prefix
    prefix = f"/registry{params.route}"
    action_path = ROUTE_ACTION_CONFIG_MAP[action].path

    return prefix + action_path


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

    for item_route_params in non_test_route_params:
        if item_route_params.subtype == item_subtype:
            return item_route_params

    raise Exception(
        f"Was not able to source route parameters for desired item_subtype = {item_subtype}")


def get_item_subtype_domain_info_example(item_subtype: ItemSubType) -> DomainInfoBase:
    # get the route params
    rp = get_item_subtype_route_params(item_subtype=item_subtype)

    # get the model
    model_class = cast(BaseModel, rp.typing_information.domain_info)

    # get the example domain info
    data = cast(BaseModel, rp.model_examples.domain_info[0])

    # make a copy and reparse to ensure the item is not a memory ref to same object
    return cast(DomainInfoBase, model_class.parse_obj(py_to_dict(data)))


def create_item(item_subtype: ItemSubType, token: str) -> Response:
    # todo replace 2 lines with get_item_subtype_dmoain_info example function and maybe in other functiosn
    params = get_item_subtype_route_params(item_subtype=item_subtype)
    domain_info = params.model_examples.domain_info[0]

    create_resp = create_item_from_domain_info(
        item_subtype=item_subtype, token=token, domain_info=domain_info)

    return create_resp


def get_route_from_item_subtype_and_action(action: RouteActions, item_subtype: ItemSubType) -> str:
    return get_route(action=action, params=get_item_subtype_route_params(item_subtype=item_subtype))


def create_item_from_domain_info(item_subtype: ItemSubType, token: str, domain_info: Any) -> Response:
    # TODO - can add check if attempting to make model run item as this should happen in prov (same thing with datasets?)

    params = get_item_subtype_route_params(item_subtype=item_subtype)
    route = config.REGISTRY_API_ENDPOINT + \
        get_route(RouteActions.CREATE, params=params)

    create_resp = requests.post(
        route,
        json=json.loads(
            domain_info.json(exclude_none=True)
        ),
        auth=BearerAuth(token)
    )

    return create_resp


def create_item_from_domain_info_successfully(item_subtype: ItemSubType, token: str, domain_info: Any) -> ItemBase:
    create_resp = create_item_from_domain_info(
        item_subtype=item_subtype, token=token, domain_info=domain_info)

    # ensure success before returning
    assert create_resp.status_code == 200, f"Non 200 code: {create_resp}, Response: {create_resp.json()}"
    create_resp = GenericCreateResponse.parse_obj(create_resp.json())
    assert create_resp.status.success, f"Unsuccessful create item. {create_resp.status}"
    assert create_resp.created_item, f"Created item not returned. {create_resp}"

    return create_resp.created_item


def create_item_successfully(item_subtype: ItemSubType, token: str) -> ItemBase:
    create_resp = create_item(item_subtype=item_subtype, token=token)

    # ensure success before returning
    assert create_resp.status_code == 200, f"Non 200 code: {create_resp}. Details: {create_resp.json()}"
    create_resp = GenericCreateResponse.parse_obj(create_resp.json())
    assert create_resp.status.success, f"Unsuccessful create item. {create_resp.status}"
    assert create_resp.created_item, f"Created item not returned. {create_resp}"
    return create_resp.created_item


def raw_create_item_successfully(item_subtype: ItemSubType, token: str) -> Dict[str, str]:
    create_resp = create_item(item_subtype=item_subtype, token=token)

    # ensure success before returning
    assert create_resp.status_code == 200, f"Non 200 code: {create_resp}"
    parsed_create_resp = GenericCreateResponse.parse_obj(create_resp.json())
    assert parsed_create_resp.status.success, f"Unsuccessful create item. {parsed_create_resp.status}"
    assert parsed_create_resp.created_item
    return create_resp.json()


id_base_list = [params.name for params in route_params]


def make_specialised_list(action: str) -> List[str]:
    """    make_specialised_list
        Given an action name, prepends action name in nice format
        to each test name in the base id list as above.

        Arguments
        ----------
        action : str
            The action 

        Returns
        -------
         : List[str]
            New list of test names
            Format: {action}: ({existing base id})

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return [f"{action}: ({base})" for base in id_base_list]


def fetch_item(item_subtype: ItemSubType, id: str, token: str) -> Response:

    fetch_resp = requests.get(
        config.REGISTRY_API_ENDPOINT + get_route_from_item_subtype_and_action(
            action=RouteActions.FETCH, item_subtype=item_subtype),
        auth=BearerAuth(token),
        params={'id': id}
    )

    return fetch_resp


def revert_item(item_subtype: ItemSubType, id: str, history_id: int, token: str, reason: str = "Integration testing") -> Response:
    revert_resp = requests.put(
        config.REGISTRY_API_ENDPOINT + get_route_from_item_subtype_and_action(
            action=RouteActions.REVERT, item_subtype=item_subtype),
        json=py_to_dict(ItemRevertRequest(
            id=id,
            history_id=history_id,
            reason=reason
        )),
        auth=BearerAuth(token),
    )
    return revert_resp


def revert_item_successfully(item_subtype: ItemSubType, id: str, history_id: int, token: str, reason: str = "Integration testing") -> ItemRevertResponse:
    revert_resp = revert_item(
        item_subtype=item_subtype,
        id=id,
        history_id=history_id,
        token=token,
        reason=reason
    )

    assert revert_resp.status_code == 200, f"Non 200 status code. {revert_resp.status_code}"
    revert_resp = ItemRevertResponse.parse_obj(revert_resp.json())
    assert revert_resp.status.success
    return revert_resp


def raw_fetch_item_successfully(item_subtype: ItemSubType, id: str, token: str) -> Dict[str, Any]:

    fetch_resp = fetch_item(item_subtype=item_subtype, id=id, token=token)

    assert fetch_resp.status_code == 200, f"Non 200 status code. {fetch_resp.status_code}"
    parsed_fetch_resp = GenericFetchResponse.parse_obj(fetch_resp.json())
    assert parsed_fetch_resp.status.success

    return fetch_resp.json()


def fetch_item_successfully(item_subtype: ItemSubType, id: str, token: str) -> GenericFetchResponse:

    fetch_resp = fetch_item(item_subtype=item_subtype, id=id, token=token)

    assert fetch_resp.status_code == 200, f"Non 200 status code. {fetch_resp.status_code}"
    fetch_resp = GenericFetchResponse.parse_obj(fetch_resp.json())
    assert fetch_resp.status.success, f"Unsuccessful fetch. {fetch_resp.status}"

    return fetch_resp


def fetch_item_successfully_parse(item_subtype: ItemSubType, id: str, token: str, model: Type[GenericFetchResponse]) -> BaseModel:
    fetch_resp = fetch_item(item_subtype=item_subtype, id=id, token=token)
    assert fetch_resp.status_code == 200, f"Non 200 status code. {fetch_resp.status_code}"
    fetch_resp = model.parse_obj(fetch_resp.json())
    assert fetch_resp.status.success, f"Unsuccessful fetch. {fetch_resp.status}"
    return fetch_resp


def fetch_complete_person_item_successfully(id: str, token: str) -> ItemPerson:
    fetch_resp = fetch_item(
        item_subtype=ItemSubType.PERSON, id=id, token=token)

    assert fetch_resp.status_code == 200, f"Non 200 status code. {fetch_resp.status_code}"
    fetch_resp = PersonFetchResponse.parse_obj(fetch_resp.json())
    assert fetch_resp.status.success, f"Unsuccessful fetch. {fetch_resp.status}"
    person_item = fetch_resp.item
    assert person_item, f"Person item not returned. {fetch_resp}"
    assert person_item.record_type == RecordType.COMPLETE_ITEM, f"Person item not complete but is {person_item.record_type}"
    assert isinstance(
        person_item, ItemPerson), f"Person item not of type ItemPerson. {type(person_item)}"
    return person_item


class FailedEntityDelete:
    item_subtype: ItemSubType
    item_id: IdentifiedResource
    error_msg: str

    def __init__(self, item_subtype: ItemSubType, item_id: IdentifiedResource, error_msg: str) -> None:
        self.item_subtype = item_subtype
        self.item_id = item_id
        self.error_msg = error_msg

    # overide to string method.
    def __str__(self) -> str:
        return f"Itemsubtype: {self.item_subtype}. item_id: {self.item_id}. Error: {self.error_msg}."


def perform_entity_cleanup(to_clean: List[Tuple[ItemSubType, IdentifiedResource]], token: str) -> None:

    failed_cleanups: List[FailedEntityDelete] = []

    for subtype, item_id in to_clean:
        try:
            delete_item(subtype=subtype, item_id=item_id, token=token)
        except Exception as e:
            failed_cleanups.append(
                FailedEntityDelete(
                    item_subtype=subtype,
                    item_id=item_id,
                    error_msg=str(e)
                ))

    # removed all items - clear - don't want to remove the same elements
    # multiple times
    to_clean.clear()
    if len(failed_cleanups) != 0:
        display_failed_cleanups(failed_cleanups)
        assert False, "Failed to clean up all items"

    return


def delete_item(subtype: ItemSubType, item_id: IdentifiedResource, token: str) -> None:

    route = get_route_from_item_subtype_and_action(
        action=RouteActions.DELETE, item_subtype=subtype)

    delete_resp = requests.delete(
        config.REGISTRY_API_ENDPOINT + route,
        params={"id": item_id},
        auth=BearerAuth(token)
    )

    if delete_resp.status_code != 200:
        details = "NA"
        try:
            details = delete_resp.json()['detail']
        except:
            None
        raise Exception(
            f"Non 200 status code from delete: {delete_resp.status_code}. Details: {details}")

    delete_resp = StatusResponse.parse_obj(delete_resp.json())

    if not delete_resp.status.success:
        raise Exception(
            f"Item failed to delete. Err: {delete_resp.status.details}")


def set_general_access_roles(item_subtype: ItemSubType, token: str, general_access_roles: List[str], id: str) -> None:
    """Given an item and desired general access roles, will update the items
    auth config to have these general access roles

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        The item to apply general access roles to
    params : RouteParameters
        _description_
    general_access_roles : List[str]
        the desired access roles for the item
    """
    original_auth = get_auth_config(
        id=id, item_subtype=item_subtype, token=token)
    new_auth = original_auth.dict()
    new_auth["general"] = general_access_roles

    put_auth_config(id=id,
                    auth_payload=new_auth, item_subtype=item_subtype, token=token)


def get_auth_config(id: str, item_subtype: ItemSubType, token: str) -> AccessSettings:
    curr_route = get_route_from_item_subtype_and_action(
        RouteActions.AUTH_CONFIGURATION_GET, item_subtype=item_subtype)
    request_params = {'id': id}
    auth_config_get_resp = requests.get(
        config.REGISTRY_API_ENDPOINT + curr_route, params=request_params,
        auth=BearerAuth(token)
    )

    try:
        assert auth_config_get_resp.status_code == 200, f"Non 200 status code received from get auth response. {auth_config_get_resp}"
    except:
        if auth_config_get_resp.status_code == 401:
            raise PermissionError(
                "User does not have authorisation to get auth config for item")
        else:
            raise AssertionError(
                f"Non 200 status code received from get auth response. {auth_config_get_resp}")

    return AccessSettings.parse_obj(auth_config_get_resp.json())


def put_auth_config(id: str, auth_payload: Dict[str, str], item_subtype: ItemSubType, token: str) -> StatusResponse:
    curr_route = get_route_from_item_subtype_and_action(
        RouteActions.AUTH_CONFIGURATION_PUT, item_subtype=item_subtype)

    request_params = {'id': id}
    auth_config_put_resp = requests.put(
        config.REGISTRY_API_ENDPOINT + curr_route,
        params=request_params,
        json=auth_payload,
        auth=BearerAuth(token))
    try:
        assert auth_config_put_resp.status_code == 200, f"Non 200 status code received from put auth response. {auth_config_put_resp}"
    except:
        if auth_config_put_resp.status_code == 401:
            raise PermissionError(
                "user does not have authorisation to write auth config to item")
        else:
            raise AssertionError(
                f"Non 200 status code received from put auth response. {auth_config_put_resp}")
    return StatusResponse.parse_obj(auth_config_put_resp.json())


def set_group_access_roles(id: str, token: str, item_subtype: ItemSubType, group_access_roles: Dict[str, List[str]]) -> None:
    """Given desired group access roles for an item, will update the items auth
    configuration to have these group access roles.

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        The item to update the group access roles of
    params : RouteParameters
        _description_
    group_access_roles : Dict[str, List[str]]
        The updated access roles. A dict of Groups to the roles for that group.
    """
    original_auth = get_auth_config(
        id=id, item_subtype=item_subtype, token=token)
    new_auth = original_auth.dict()
    new_auth["groups"] = group_access_roles
    put_auth_config(id=id,
                    auth_payload=new_auth, item_subtype=item_subtype, token=token)


def add_group_access_roles(id: str, token: str, item_subtype: ItemSubType, group_access_roles: Dict[str, List[str]]) -> None:
    """Given desired additional group access roles for an item, will update the items auth
    configuration to have these group access roles as well as the original .

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        The item to update the group access roles of
    params : RouteParameters
        _description_
    group_access_roles : Dict[str, List[str]]
        The access roles to add. A dict of Groups to the roles for that group.
    """
    original_auth = get_auth_config(
        id=id, item_subtype=item_subtype, token=token)
    new_auth = original_auth.dict()
    # merge and overwrite with new ones if overlap.
    new_auth["groups"] = original_auth.groups | group_access_roles
    put_auth_config(id=id,
                    auth_payload=new_auth, item_subtype=item_subtype, token=token)


def remove_general_access_from_item(id: str, item_subtype: ItemSubType, token: str) -> None:
    """removes general access reasd and write form the provided item.

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(id=id,
                             item_subtype=item_subtype, general_access_roles=[], token=token)


def give_general_read_access(id: str, item_subtype: ItemSubType, token: str) -> None:
    """Gives general access for metadata read for the provided item

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(
        id=id, item_subtype=item_subtype, general_access_roles=['metadata-read'], token=token)


def give_general_read_write_access(id: str, item_subtype: ItemSubType, token: str) -> None:
    """Give general read and write access to the provided item

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(id=id, item_subtype=item_subtype, general_access_roles=[
                             'metadata-read', 'metadata-write'], token=token)


def accessible_via_registry_fetch(id: str, token: str, item_subtype: ItemSubType) -> bool:
    fetch_resp = fetch_item(item_subtype=item_subtype, id=id, token=token)

    if fetch_resp.status_code == 401:
        return False

    if fetch_resp.status_code == 200:
        fetch = GenericFetchResponse.parse_obj(fetch_resp.json())

        # check status as returns 200 if item doesnt exist.
        if fetch.status.success:
            return True
        else:
            return False

    raise Exception(
        f"Unexpected status code recieved: {fetch_resp.status_code}. Item was not accessible, nor was it successfully found and access denied")


def accessible_via_registry_list(item_id: str, token: str) -> bool:
    # maybe dont use this for integration tests (slow) and instead use a
    # "accessible via registry fetch instead" or... optimise this.

    # returns true if an item is accessible in the registry via list endpoint.
    # used to check the registry general list respects authorisation rights.
    # could be sped up by not doing exhaustive search then checking, but by doing search by pages
    # and possibly returning early if item is found.

    return item_id in set(ItemBase.parse_obj(item).id for item in general_list_exhaust(token=token))


def general_list_exhaust(token: str, general_list_request: Optional[GeneralListRequest] = None) -> List[Dict[str, Any]]:
    """
    general_list_exhaust 

    Uses the default filter/sort options to repeatedly query the general list
    endpoint until exhaustion.

    Parameters
    ----------
    client : TestClient
        FastAPI test client

    Returns
    -------
    List[Dict[str, Any]]
        The item list
    """
    exhausted = False
    pagination_key: Optional[PaginationKey] = None
    items: List[Dict[str, Any]] = []

    base_request: GeneralListRequest

    if general_list_request:
        base_request = general_list_request
    else:
        base_request = GeneralListRequest(
            pagination_key=pagination_key
        )

    while not exhausted:
        base_request.pagination_key = pagination_key
        response = requests.post(config.REGISTRY_API_ENDPOINT + "/registry/general/list",
                                 json=json.loads(base_request.json()),
                                 auth=BearerAuth(token)
                                 )

        # checks that the response was successful and parsable
        check_status_success_true(response)
        json_response = response.json()
        parsed_response = PaginatedListResponse.parse_obj(json_response)
        assert parsed_response.items is not None, "items should not be None"

        # add the items to accumulated items
        items.extend(parsed_response.items)

        pagination_key = parsed_response.pagination_key
        if pagination_key is None:
            exhausted = True

    return items


def general_list_first_n(token: str, first_num: int,  general_list_request: Optional[GeneralListRequest] = None) -> List[Dict[str, Any]]:
    """
    general_list_first_n 

    Uses the default filter/sort options to repeatedly query the general list
    endpoint until the desired number of items are obtained.

    Parameters
    ----------
    client : TestClient
        FastAPI test client

    Returns
    -------
    List[Dict[str, Any]]
        The item list
    """
    pagination_key: Optional[PaginationKey] = None
    items: List[Dict[str, Any]] = []

    base_request: GeneralListRequest

    if general_list_request:
        base_request = general_list_request
    else:
        base_request = GeneralListRequest(
            pagination_key=pagination_key
        )
    exhausted = False
    while len(items) < first_num and not exhausted:
        base_request.pagination_key = pagination_key
        response = requests.post(config.REGISTRY_API_ENDPOINT + "/registry/general/list",
                                 json=json.loads(base_request.json()),
                                 auth=BearerAuth(token)
                                 )

        # checks that the response was successful and parsable
        check_status_success_true(response)
        json_response = response.json()
        parsed_response = PaginatedListResponse.parse_obj(json_response)
        assert parsed_response.items is not None, "items should not be None"

        # add the items to accumulated items
        items.extend(parsed_response.items)

        pagination_key = parsed_response.pagination_key
        if pagination_key is None:
            exhausted = True

    return items[:first_num]


def check_status_success_true(response: Response) -> None:
    """
    Asserts that:
    - the response has status code 200
    - the response is parsable as a StatusResponse
    - the response has status.success == True

    Parameters
    ----------
    response : Response
        The requests response
    """
    assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.text}"
    status_response = StatusResponse.parse_obj(response.json())
    assert status_response.status.success, f"Response {response} should have had status.success == True but was false."


def fetch_lock_history(id: str, item_subtype: ItemSubType, token: str) -> LockHistoryResponse:
    """Fetches the lock history of an item

    Parameters
    ----------
    client : TestClient
        _description_
    id : the item's id to fetch the lock history of.
        _description_
    params : RouteParameters
        _description_

    Returns
    -------
    LockHistoryResponse
        _description_
    """
    curr_route = get_route_from_item_subtype_and_action(
        RouteActions.LOCK_HISTORY, item_subtype=item_subtype)
    request_params = {'id': id}
    lock_hist_resp = requests.get(
        config.REGISTRY_API_ENDPOINT + curr_route, params=request_params,
        auth=BearerAuth(token))
    assert lock_hist_resp.status_code == 200, f"Non 200 response code: {lock_hist_resp.status_code}. Details: {lock_hist_resp.text}"
    return LockHistoryResponse.parse_obj(lock_hist_resp.json())


def unlock_item(id: str, item_subtype: ItemSubType, token: str) -> StatusResponse:
    curr_route = get_route_from_item_subtype_and_action(
        item_subtype=item_subtype, action=RouteActions.UNLOCK)
    json_payload = {
        "id": id,
        "reason": "testing unlock functionality in integration test"
    }

    unlock_resp = requests.put(
        config.REGISTRY_API_ENDPOINT + curr_route, json=json_payload,
        auth=BearerAuth(token))
    assert unlock_resp.status_code == 200, f"Non 200 response code form unlock response: {unlock_resp.status_code}. Details: {unlock_resp.text}"
    unlock_resp = StatusResponse.parse_obj(unlock_resp.json())
    return unlock_resp


def update_item(id: str, updated_domain_info: Any, item_subtype: ItemSubType, token: str, reason: str = "Integration testing") -> Response:
    update_route = get_route_from_item_subtype_and_action(
        action=RouteActions.UPDATE, item_subtype=item_subtype)
    update_item_resp = requests.put(
        config.REGISTRY_API_ENDPOINT + update_route,
        params={'id': id, 'reason': reason},
        json=json.loads(updated_domain_info.json(exclude_none=True)),
        auth=BearerAuth(token)
    )
    return update_item_resp


def parsed_successful_update_item(id: str, updated_domain_info: Any, item_subtype: ItemSubType, token: str, reason: str = "Integration testing") -> UpdateResponse:
    resp = update_item(
        id=id,
        updated_domain_info=updated_domain_info,
        item_subtype=item_subtype,
        token=token,
        reason=reason
    )
    assert resp.status_code == 200, f"Non 200 status code {resp.status_code}. Info {resp.text}."
    parsed = UpdateResponse.parse_obj(resp.json())

    assert parsed.status.success, f"Non success from update, details: {parsed.status.details}"
    return parsed


def get_lock_status(id: str, item_subtype: ItemSubType, token: str) -> LockStatusResponse:
    request_params = {"id": id}
    curr_route = get_route_from_item_subtype_and_action(
        item_subtype=item_subtype, action=RouteActions.LOCKED)
    lock_status_resp = requests.get(
        config.REGISTRY_API_ENDPOINT + curr_route,
        params=request_params,
        auth=BearerAuth(token)
    )
    assert lock_status_resp.status_code == 200, f"Non 200 response code from lock status response: {lock_status_resp.status_code}. Details: {lock_status_resp.text}"
    lock_status_resp = LockStatusResponse.parse_obj(lock_status_resp.json())
    return lock_status_resp


def lock_item(id: str, item_subtype: ItemSubType, token: str) -> StatusResponse:
    curr_route = get_route_from_item_subtype_and_action(
        item_subtype=item_subtype, action=RouteActions.LOCK)
    json_payload = {
        "id": id,
        "reason": "testing lock functionality"
    }

    lock_resp = requests.put(
        config.REGISTRY_API_ENDPOINT + curr_route,
        json=json_payload,
        auth=BearerAuth(token)
    )
    assert lock_resp.status_code == 200, f"Non 200 response code from lock response: {lock_resp.status_code}. Details: {lock_resp.text}"
    lock_resp = StatusResponse.parse_obj(lock_resp.json())
    return lock_resp


def check_item_created_timestamp_sorting_and_type(items: List[ItemBase], ascending: Optional[bool] = None, subtype: Optional[ItemSubType] = None) -> None:
    if ascending is not None:
        # check correct order
        for i in range(len(items)-1):
            if ascending:
                assert items[i].created_timestamp <= items[i +
                                                           1].created_timestamp, f"items[{i}].created_timestamp ({items[i].created_timestamp}) should be less than or equal to items[{i+1}].created_timestamp ({items[i+1].created_timestamp})"
            else:
                assert items[i].created_timestamp >= items[i +
                                                           1].created_timestamp, f"items[{i}].created_timestamp ({items[i].created_timestamp}) should be greater than or equal to items[{i+1}].created_timestamp ({items[i+1].created_timestamp})"

    if subtype:
        for item in items:
            assert item.item_subtype == subtype, f"item.item_subtype ({item.item_subtype}) should be {subtype}"


def version_item(id: str, token: str, item_subtype: ItemSubType, reason: str = "Integration testing") -> Response:
    version_route = get_route_from_item_subtype_and_action(
        action=RouteActions.VERSION, item_subtype=item_subtype)
    req = py_to_dict(VersionRequest(id=id, reason=reason))
    version_resp = requests.post(
        url=config.REGISTRY_API_ENDPOINT + version_route,
        json=req,
        auth=BearerAuth(token)
    )
    return version_resp


def parsed_version_item(id: str, token: str, item_subtype: ItemSubType, reason: str = "Integration testing") -> VersionResponse:
    raw = version_item(id=id, token=token,
                       item_subtype=item_subtype, reason=reason)
    assert raw.status_code == 200, f"Non 200 status code {raw.status_code}. Res: {raw.text}."
    return VersionResponse.parse_obj(raw.json())


def fail_version_item(id: str, token: str, item_subtype: ItemSubType, reason: str = "Integration testing", expected_code: Optional[int] = 400) -> Response:
    raw = version_item(id=id, token=token,
                       item_subtype=item_subtype, reason=reason)

    if expected_code is not None:
        assert raw.status_code == expected_code, f"Non {expected_code} status code {raw.status_code}. Res: {raw.text}."
    else:
        assert raw.status_code != 200, f"200 status code. Expected failure. Res: {raw.text}."

    return raw


def seed_item(token: str, item_subtype: ItemSubType) -> Response:
    seed_route = get_route_from_item_subtype_and_action(
        action=RouteActions.SEED, item_subtype=item_subtype)
    seed_resp = requests.post(
        url=config.REGISTRY_API_ENDPOINT + seed_route,
        auth=BearerAuth(token)
    )
    return seed_resp


def parsed_seed_item(token: str, item_subtype: ItemSubType, model: Type[GenericSeedResponse]) -> GenericSeedResponse:
    raw = seed_item(token=token,
                    item_subtype=item_subtype)
    assert raw.status_code == 200, f"Non 200 status code {raw.status_code}. Res: {raw.text}."
    return model.parse_obj(raw.json())


def fail_seed_item(token: str, item_subtype: ItemSubType,  expected_code: Optional[int] = 400) -> Response:
    raw = seed_item(token=token,
                    item_subtype=item_subtype)

    if expected_code is not None:
        assert raw.status_code == expected_code, f"Non {expected_code} status code {raw.status_code}. Res: {raw.text}."
    else:
        assert raw.status_code != 200, f"200 status code. Expected failure. Res: {raw.text}."

    return raw


def check_ids_in_list_resp(ids: List[str], list_resp: List[Dict[str, Any]]) -> bool:
    """Returns true if all id's in ids are found in the list of items.

    Parameters
    ----------
    ids : List[str]
        List of ids to check the presence of in list resp
    list_resp : List[Dict[str, Any]]


    Returns
    -------
    bool
        True if all ids present.
    """

    ids_in_list = set(item['id'] for item in list_resp)

    for id in ids:
        if id not in ids_in_list:
            return False

    return True
