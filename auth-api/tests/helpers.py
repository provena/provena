from typing import Dict, Any, List, Union
from copy import deepcopy
from tests.config import *
from fastapi.testclient import TestClient
from httpx import Response
from random import choice
import json
from pydantic import BaseModel
from ProvenaInterfaces.SharedTypes import StatusResponse
from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.DataStoreAPI import *
import random


def parse_status_response(response: Any, model: Any) -> Any:
    if not response.status_code == 200:
        try:
            details = response.json()['detail']
        except:
            details = "Unknown"
        assert False, f"Non 200 code: {response.status_code}. Error details {details}."

    json_response = response.json()
    status_response = StatusResponse.parse_obj(json_response)
    assert status_response.status.success, f"Success was false, details: {status_response.status.details}."

    # parse as specified model
    return model.parse_obj(json_response)


def setup_user_group_table(client: Any, table_name: str) -> None:
    # Setup dynamo db
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )


def setup_link_table(botoclient: Any, table_name: str, gsi_name: str) -> None:
    # Setup dynamo db
    botoclient.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'person_id',
                'AttributeType': 'S'
            },
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'username',
                'KeyType': 'HASH'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': gsi_name,
                'KeySchema': [
                    {
                        'AttributeName': 'person_id',
                        'KeyType': 'HASH'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
            },
        ],
        BillingMode='PAY_PER_REQUEST'
    )


def generate_fake_id() -> int:
    return random.randint(0, 9999999999)


def generate_fake_group() -> UserGroupMetadata:
    rand_id = generate_fake_id()
    return UserGroupMetadata(
        id=f"Group{rand_id}",
        display_name=f"Group ID {rand_id}",
        description=f"Fake group with ID {rand_id}."
    )


def generate_fake_user() -> GroupUser:
    rand_id = generate_fake_id()
    return GroupUser(
        username=f"email{rand_id}@fake.com",
        email=f"email{rand_id}@fake.com"
    )


def populate_table_with_groups(test_client: TestClient, groups: List[UserGroupMetadata]) -> None:
    for group in groups:
        payload = json.loads(group.json())
        response = test_client.post(
            group_admin_endpoints.ADD_GROUP, json=payload)
        assert response.status_code == 200
        status = AddGroupResponse.parse_obj(response.json()).status
        assert status.success


def setup_n_empty_groups(test_client: TestClient, count: int) -> List[UserGroupMetadata]:
    groups: List[UserGroupMetadata] = [generate_fake_group()
                                       for _ in range(count)]
    populate_table_with_groups(test_client=test_client, groups=groups)
    return groups


def setup_n_populated_groups(test_client: TestClient, group_count: int, user_count: int) -> List[UserGroup]:
    empty_groups: List[UserGroupMetadata] = [generate_fake_group()
                                             for _ in range(group_count)]
    populate_table_with_groups(test_client, empty_groups)

    full_groups: List[UserGroup] = []

    for group in empty_groups:
        users: List[GroupUser] = [
            generate_fake_user() for _ in range(user_count)]
        for user in users:
            _ = parse_status_response(
                response=test_client.post(
                    group_admin_endpoints.ADD_MEMBER,
                    params={
                        'group_id': group.id
                    },
                    json=json.loads(user.json())
                ),
                model=AddMemberResponse
            )
        populated_group: ListMembersResponse = parse_status_response(
            response=test_client.get(
                group_admin_endpoints.LIST_MEMBERS,
                params={
                    'id': group.id
                }
            ),
            model=ListMembersResponse
        )

        assert populated_group.group is not None
        assert len(populated_group.group.users) == user_count
        full_groups.append(populated_group.group)

    return full_groups


def write_random_group(test_client: TestClient, user_count: int = default_user_count) -> UserGroup:
    groups = setup_n_populated_groups(
        test_client=test_client, group_count=1, user_count=user_count)
    return groups[0]


def filtered_none_deep_copy(input: Any) -> Union[Dict[Any, Any], List[Any], Any]:
    """
    Helper function to make a deepcopy of a dictionary recursively - not
    including any None objects. This is because dictionary comparisons are
    sensitive to None/null values in the pydantic model/json object. We aren't
    concerned about Nones vs not including for the purposes of these test.

    Parameters
    ----------
    input : Any
        Either a dictionary or an object which will be returned (think leaf
        node)

    Returns
    -------
    Union[Dict[Any, Any], Any]
        Either a dictionary (i.e. recursively) or a leaf node
    """
    # if dictionary - copy recursively
    if isinstance(input, dict):
        # produce a new dictionary
        new_dict: Dict[Any, Any] = {}
        # iterate through key values
        for k, v in input.items():
            # if none - don't include
            if v is None or v == "null":
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_dict[k] = filtered_none_deep_copy(v)
        return new_dict

    # if list - iterate through and filter none
    # returning recursively for elements
    if isinstance(input, list):
        new_list = []
        for v in input:
            # if none - don't include
            if v is None:
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_list.append(filtered_none_deep_copy(v))
        return new_list
    else:
        # Return a native copy of the leaf node
        return deepcopy(input)


def smart_model_compare(model1: Any, model2: Any) -> bool:
    return filtered_none_deep_copy(model1.dict()) == filtered_none_deep_copy(model2.dict())


def smart_raw_compare(obj1: Any, obj2: Any) -> bool:
    return filtered_none_deep_copy(obj1) == filtered_none_deep_copy(obj2)


def setup_dynamodb_groups_table(client: Any, table_name: str) -> None:
    """    setup_dynamob_groups_table
        Use boto client to produce dynamodb table which mirrors
        the groups table for testing

        Arguments
        ----------
        client: dynamodb boto client
            The mocked dynamo db client
        table_name : str
            The name of the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Setup dynamo db
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )


def create_dynamodb_table(ddb_client: Any, table_name: str) -> None:
    """
    Given a dynamodb client and table name, will produce a dynamo table which is
    compatible with the groups table.

    Parameters
    ----------
    ddb_client : Any
        The boto client
    table_name : str, optional
        The name of the table to create, by default test_groups_name
    """
    # Setup the mock groups table
    setup_dynamodb_groups_table(
        client=ddb_client,
        table_name=table_name
    )


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
    assert response.status_code == 200
    status_response = StatusResponse.parse_obj(response.json())
    assert status_response.status.success, f"Response {response} should have had status.success == True but was false."


def check_status_success_false(response: Response) -> None:
    """
    Asserts that:
    - the response has status code 200
    - the response is parsable as a StatusResponse
    - the response has status.success == False

    Parameters
    ----------
    response : Response
        The requests response
    """
    assert response.status_code == 200
    status_response = StatusResponse.parse_obj(response.json())
    assert not status_response.status.success, f"Response {response} should have had status.success == False but was true."


def check_exported_table_size(test_client: TestClient, expected_size: int) -> List[Dict[str, Any]]:
    """
    Uses the specified fastAPI test client to run an admin export of the current
    table, verifying that the number of items is equal to the expected size.

    Parameters
    ----------
    test_client : TestClient
        The FastAPI test client
    expected_size : int
        The expected size.

    Returns
    -------
    List[Dict[str, Any]]
        Returns the items
    """
    response = test_client.get(admin_export_endpoint)
    check_status_success_true(response)
    exported_response = GroupsExportResponse.parse_obj(response.json())
    exported_items = exported_response.items
    assert exported_items is not None
    assert len(exported_items) == expected_size
    return exported_items


def assert_groups_state(test_client: TestClient, groups_state: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Uses the admin export endpoint to check that the current state of the
    groups is exactly equivalent to the expected groups state (as a list of
    untyped items)

    Parameters
    ----------
    test_client : TestClient
        The test client to use
    groups_state : List[Dict[str, Any]]
        The expected groups state

    Returns
    -------
    Dict[str, Dict[str, Any]]
        A mapping between id -> item in the exported items
    """
    # use an admin export to get current items and check size
    current_items = check_exported_table_size(
        test_client=test_client,
        expected_size=len(groups_state)
    )

    # pull out the id -> item maps
    expected_id_map: Dict[str, Dict[str, Any]] = {}
    actual_id_map: Dict[str, Dict[str, Any]] = {}

    for item in groups_state:
        expected_id_map[item['id']] = item
    for item in current_items:
        actual_id_map[item['id']] = item

    # check ID sets are equal
    assert set(expected_id_map.keys()) == set(actual_id_map.keys())

    # check that each item is equal
    for expected_id, expected_item in expected_id_map.items():
        actual_item = actual_id_map[expected_id]
        assert filtered_none_deep_copy(
            actual_item) == filtered_none_deep_copy(expected_item)

    return actual_id_map


def produce_modified_items(input_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For a list of untyped items in the groups table, updates the display name to
    indicate modification. Make sure that the dictionary has a display_name
    attribute. 

    NOTE this will change the actual items - it does not make a copy

    Parameters
    ----------
    input_items : List[Dict[str, Any]]
        The list of input items to change.

    Returns
    -------
    List[Dict[str, Any]]
        The output modified list
    """
    for input_item in input_items:
        input_item['description'] = input_item['description'] + " modified"
    return input_items


def item_base_dict_to_import_format(user_group_dict: Dict[str, UserGroup]) -> List[Dict[str, Any]]:
    """
    Converts from the response format from setup_tables -> the recommended
    import payload format. This is to enable easy integration with the import
    request objects.

    Parameters
    ----------
    itemBase_dict : Dict[str, ItemBase]
        A mapping of id -> ItemBase 

    Returns
    -------
    List[Dict[str, Any]]
        A list of entries in this mapping, expressed as safe JSON dicts
    """
    return_dict_list = []

    for item_base in user_group_dict.values():
        return_dict_list.append(json.loads(item_base.json(exclude_none=True)))

    return return_dict_list


def get_required_fields(pydantic_model: BaseModel) -> List[str]:
    """
    Given a pydantic model, iterates through the fields of the model itself (not
    an instance) and returns a list of keys which are required.

    Parameters
    ----------
    pydantic_model : BaseModel
        The pydantic model to explore

    Returns
    -------
    List[str]
        List of model KEYS which are required
    """
    # analyse the model to find keys which are required
    required_fields: List[str] = []

    # loop through key/field combinations
    for field_key, model_field in pydantic_model.__fields__.items():
        # add to list if required
        if model_field.required:
            required_fields.append(field_key)

    return required_fields
