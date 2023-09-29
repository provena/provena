from typing import List
from tests.config import Config
import requests
from requests import Response
from KeycloakRestUtilities.Token import BearerAuth
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.RegistryModels import *
from tests.helpers.general_helpers import py_to_dict
from tests.helpers.general_helpers import assert_200_ok, assert_x_ok
from tests.helpers.registry_helpers import fetch_item_successfully_parse

def request_dataset_review_desired_status_code(
        release_approval_request: ReleaseApprovalRequest,
        token: str,
        config: Config,
        desired_status_code: int,
) -> Response: 
    endpoint = config.DATA_STORE_API_ENDPOINT + "/release/approval-request"

    resp = requests.post(
        endpoint,
        json=py_to_dict(release_approval_request),
        auth=BearerAuth(token)
    )

    assert_x_ok(res=resp, desired_status_code=desired_status_code) 
    return resp


def action_review_request_desired_status_code(
        action_request: ActionApprovalRequest,
        token: str,
        config: Config,
        desired_status_code: int,
) -> Response:
    
    endpoint = config.DATA_STORE_API_ENDPOINT + "/release/action-approval-request"

    resp = requests.put(
        endpoint,
        json=py_to_dict(action_request),
        auth=BearerAuth(token)
    )

    assert_x_ok(res=resp, desired_status_code=desired_status_code) 

    return resp


def perform_reviewers_table_cleanup(ids: List[str], token: str, config: Config) -> None:

    for id in ids:
        try:
            remove_id_from_reviewers_table(token=token, id=id, config=config)
        except Exception as e:
            print(f"Failed to remove {id} from reviewers table. Details: {e}")

def remove_id_from_reviewers_table(token: str, id: str, config: Config) -> None:

    delete_reviewer_endpoint = config.DATA_STORE_API_ENDPOINT + "/release/sys-reviewers/delete"

    resp = requests.delete(
        delete_reviewer_endpoint,
        params = {"reviewer_id":id},
        auth=BearerAuth(token)
    )
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}. Details: {resp.text}"


def add_id_to_reviewers_table(token: str, id: str, config: Config) -> None:

    add_reviewer_endpoint = config.DATA_STORE_API_ENDPOINT + "/release/sys-reviewers/add"

    resp = requests.post(
        add_reviewer_endpoint,
        params = {"reviewer_id":id},
        auth=BearerAuth(token)
    )

    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}. Details: {resp.text}"
    

def remove_id_from_reviewers_table_and_check(token: str, id: str, config: Config) -> None:
    
        remove_id_from_reviewers_table(token=token, id=id, config=config)
        
        if id_in_reviewers_table(token=token, id=id, config=config):
            raise Exception(f"Failed to remove {id} from reviewers table")
        

def add_id_to_reviewers_table_and_check(token: str, id: str, config: Config) -> None:

    add_id_to_reviewers_table(token=token, id=id, config=config)
    
    if not id_in_reviewers_table(token=token, id=id, config=config):
        raise Exception(f"Failed to add {id} to reviewers table")


def id_in_reviewers_table(token: str, id: str, config: Config) -> bool:
    # list all reviewers using the list endpoit
    endpoint = config.DATA_STORE_API_ENDPOINT + "/release/sys-reviewers/list"
    resp = requests.get(
        endpoint,
        auth=BearerAuth(token)
    )

    ids = resp.json()
    return id in ids 

def fetch_and_assert_successful_review_request(release_request: ReleaseApprovalRequest, token: str, expected_released_status: ReleasedStatus) -> None:
    
    fetch_resp = fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET,
        id=release_request.dataset_id,
        token=token,
        model=DatasetFetchResponse
    )
    assert isinstance(fetch_resp, DatasetFetchResponse),f"Expected DatasetFetchResponse, got {type(fetch_resp)}"
    dataset = fetch_resp.item
    assert isinstance(dataset, ItemDataset), f"Expected ItemDataset, got {type(dataset)}"

    assert dataset.release_status == expected_released_status, f"Expected release status to be pending, got {dataset.release_status}"
    # will have release_approver even if was rejected
    assert dataset.release_approver == release_request.approver_id, f"Expected release approver to be {release_request.approver_id}, got {dataset.release_approver}"
    assert dataset.release_timestamp is not None, f"Expected release timestamp to be set, got {dataset.release_timestamp}"
    assert len(dataset.release_history)>0, f"Expected release history to have >0 entries, got {len(dataset.release_history)}"
    # always check most recent
    assert dataset.release_history[-1].approver == release_request.approver_id, f"Expected release history approver to be {release_request.approver_id}, got {dataset.release_history[0].approver}"
    assert dataset.release_history[-1].notes == release_request.notes, f"Expected release history notes to be {release_request.notes}, got {dataset.release_history[0].notes}"
    assert dataset.release_history[-1].action == STATUS_TO_HISTORY_ACTION_MAP[expected_released_status], f"Expected release history action to be {ReleaseAction.REQUEST}, got {dataset.release_history[0].action}"


def fetch_and_assert_successful_action_review_request(action_request: ActionApprovalRequest, token: str, expected_released_status: ReleasedStatus) -> None:
    
    fetch_resp = fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET,
        id=action_request.dataset_id,
        token=token,
        model=DatasetFetchResponse
    )
    assert isinstance(fetch_resp, DatasetFetchResponse),f"Expected DatasetFetchResponse, got {type(fetch_resp)}"
    dataset = fetch_resp.item
    assert isinstance(dataset, ItemDataset), f"Expected ItemDataset, got {type(dataset)}"

    assert dataset.release_status == expected_released_status, f"Expected release status to be pending, got {dataset.release_status}"
    # will have release_approver even if was rejected
    assert dataset.release_timestamp is not None, f"Expected release timestamp to be set, got {dataset.release_timestamp}"
    assert len(dataset.release_history)>0, f"Expected release history to have >0 entries, got {len(dataset.release_history)}"
    # always check most recent
    assert dataset.release_history[-1].notes == action_request.notes, f"Expected release history notes to be {action_request.notes}, got {dataset.release_history[0].notes}"
    assert dataset.release_history[-1].action == STATUS_TO_HISTORY_ACTION_MAP[expected_released_status], f"Expected release history action to be {ReleaseAction.REQUEST}, got {dataset.release_history[0].action}"




STATUS_TO_HISTORY_ACTION_MAP = {
    ReleasedStatus.PENDING: ReleaseAction.REQUEST,
    ReleasedStatus.RELEASED: ReleaseAction.APPROVE,
    # NOT_RELEASE status goes to REJECT action ( note that not released and also be a status with 0 history entries)
    ReleasedStatus.NOT_RELEASED: ReleaseAction.REJECT,
}