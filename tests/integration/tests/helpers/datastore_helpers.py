from SharedInterfaces.DataStoreAPI import *
from typing import Optional
import json
import requests
from KeycloakRestUtilities.Token import BearerAuth
from tests.helpers.registry_helpers import fetch_item_successfully_parse, get_item_subtype_domain_info_example
from tests.config import config
from SharedInterfaces.RegistryModels import ItemSubType, DatasetDomainInfo
from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.DataStoreAPI import *
from requests import Response
from tests.helpers.general_helpers import py_to_dict


def mint_basic_dataset_successfully(token: str,  author_organisation_id: str, publisher_organisation_id: str, model: Optional[DatasetDomainInfo] = None) -> MintResponse:
    # need to make sure that the token user is linked in the link service to a Person

    # payload form registrymodel examples test.
    if model is None:
        dataset_domain_info = get_item_subtype_domain_info_example(
            item_subtype=ItemSubType.DATASET)
        dataset_domain_info = DatasetDomainInfo.parse_obj(
            dataset_domain_info.dict())
    else:
        dataset_domain_info = model

    # update the domain info to use the specified IDs
    dataset_domain_info.collection_format.associations.organisation_id = author_organisation_id
    dataset_domain_info.collection_format.dataset_info.publisher_id = publisher_organisation_id

    # use collection format
    dataset_payload = json.loads(
        dataset_domain_info.collection_format.json(exclude_none=True))

    response = requests.post(
        config.DATA_STORE_API_ENDPOINT + "/register/mint-dataset",
        auth=BearerAuth(token),
        json=dataset_payload,
    )
    assert response.status_code == 200, f"Recieved non 200 status code ({response.status_code}) to mint dataset. Details: {response.json()}"
    mint_response = MintResponse.parse_obj(response.json())
    assert mint_response.status.success, f"Mint failed with error: {mint_response.status.details}."
    handle = mint_response.handle
    assert handle, "Mint response did not contain a handle."

    return mint_response


def generate_read_creds(dataset_id: str, token: str) -> Response:

    resp = requests.post(
        config.DATA_STORE_API_ENDPOINT +
        "/registry/credentials/generate-read-access-credentials",
        auth=BearerAuth(token),
        json={
            "dataset_id": dataset_id,
            "console_session_required": True  # not sure what this is
        }
    )
    return resp


def generate_read_creds_successfully(dataset_id: str, token: str) -> CredentialResponse:

    resp = generate_read_creds(dataset_id=dataset_id, token=token)
    assert resp.status_code == 200, f"Recieved non 200 status code ({resp.status_code}) to generate read credentials. Details: {resp.json()}"
    resp = CredentialResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to generate read creds with error: {resp.status.details}"
    return resp


def generate_write_creds(dataset_id: str, token: str) -> Response:

    resp = requests.post(
        config.DATA_STORE_API_ENDPOINT +
        "/registry/credentials/generate-write-access-credentials",
        auth=BearerAuth(token),
        json={
            "dataset_id": dataset_id,
            "console_session_required": True  # not sure what this is
        }
    )
    return resp


def generate_write_creds_assert_status_code(dataset_id: str, token: str, desired_status_code: int) -> Response:

    resp = generate_write_creds(dataset_id=dataset_id, token=token)
    assert resp.status_code == desired_status_code, f"Recieved non {desired_status_code} status code ({resp.status_code}) to generate write credentials. Details: {resp.json()}"
    return resp


def generate_write_creds_successfully(dataset_id: str, token: str) -> CredentialResponse:

    resp = generate_write_creds(dataset_id=dataset_id, token=token)
    assert resp.status_code == 200, f"Recieved non 200 status code ({resp.status_code}) to generate write credentials. Details: {resp.json()}"
    resp = CredentialResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to generate write creds with error: {resp.status.details}"
    return resp


def update_metadata_sucessfully(dataset_id: str, updated_metadata: Dict[str, str], token: str, reason: str = "Integration testing") -> UpdateMetadataResponse:
    response = requests.post(
        config.DATA_STORE_API_ENDPOINT + '/register/update-metadata',
        params={'handle_id': dataset_id, 'reason': reason},
        json=updated_metadata,
        auth=BearerAuth(token),
    )
    assert response.status_code == 200, f"Recieved non 200 status code ({response.status_code}) to update metadata. Details: {response.json()}"
    update_metadata_response = UpdateMetadataResponse.parse_obj(
        response.json())
    assert update_metadata_response.status.success, f"Failed to update metadata with error: {update_metadata_response.status.details}"

    return update_metadata_response


def revert_dataset_successfully(dataset_id: str, history_id: int, token: str, reason: str = "Integration testing") -> ItemRevertResponse:
    revert_request = ItemRevertRequest(
        id=dataset_id,
        history_id=history_id,
        reason=reason
    )
    endpoint = config.DATA_STORE_API_ENDPOINT + '/register/revert-metadata'
    response = requests.put(
        url=endpoint,
        json=py_to_dict(revert_request),
        auth=BearerAuth(token),
    )
    assert response.status_code == 200, f"Failed to revert, status code {response.status_code}. Text: {response.text}"
    revert_metadata_response = ItemRevertResponse.parse_obj(
        response.json())
    assert revert_metadata_response.status.success
    return revert_metadata_response


def ds_version_item(id: str, token: str, reason: str = "Integration testing") -> Response:
    version_route = config.DATA_STORE_API_ENDPOINT + "/register/version"
    req = py_to_dict(VersionRequest(id=id, reason=reason))
    version_resp = requests.post(
        url=version_route,
        json=req,
        auth=BearerAuth(token)
    )
    return version_resp


def ds_parsed_version_item(id: str, token: str, reason: str = "Integration testing") -> VersionResponse:
    raw = ds_version_item(id=id, token=token,
                          reason=reason)
    assert raw.status_code == 200, f"Non 200 status code {raw.status_code}. Res: {raw.text}."
    return VersionResponse.parse_obj(raw.json())


def ds_fail_version_item(id: str, token: str, reason: str = "Integration testing", expected_code: Optional[int] = 400) -> Response:
    raw = ds_version_item(id=id, token=token,
                          reason=reason)

    if expected_code is not None:
        assert raw.status_code == expected_code, f"Non {expected_code} status code {raw.status_code}. Res: {raw.text}."
    else:
        assert raw.status_code != 200, f"200 status code. Expected failure. Res: {raw.text}."

    return raw

def get_presigned_url_status_code(pre_signed_url_req: PresignedURLRequest, token: str, desired_status_code: int) -> Response:
    resp = requests.post(
        config.DATA_STORE_API_ENDPOINT + "/registry/items/generate-presigned-url",
        auth=BearerAuth(token),
        json=py_to_dict(pre_signed_url_req)
    )

    assert resp.status_code == desired_status_code, f"Desired status code {desired_status_code} not recieved. Recieved {resp.status_code}. Response: {resp.text}"
    return resp


def get_presigned_url_successfully(pre_signed_url_req: PresignedURLRequest, token: str) -> PresignedURLResponse:
        resp = get_presigned_url_status_code(pre_signed_url_req=pre_signed_url_req, token=token, desired_status_code=200)
        url_resp = PresignedURLResponse.parse_obj(resp.json())
        
        # to ensure success we must attempt download as the request will respond with a link (that 
        # wont work) if request is invalid (for particular reasons), so we must test this.

        url = url_resp.presigned_url
        assert url, "Presigned url response did not contain a presigned url."

        # will be 403 for attempted to download file with path outside of scope of dataset id's valid paths
        fetch_url_content(url=url, desired_status_code=200) 

        return url_resp




def fetch_url_content(url: str, desired_status_code: int = 200) -> Dict[str, str]:
    resp = requests.get(url=url)
    assert resp.status_code == desired_status_code, f"Desired status code {desired_status_code} not recieved. Recieved {resp.status_code}. Response: {resp.text}"
    return resp.json()
    


def fetch_dataset_metadata(dataset_id: str, token: str) -> Dict[str, str]:
    
    fetch_resp = fetch_item_successfully_parse(item_subtype=ItemSubType.DATASET, id=dataset_id, token=token, model=DatasetFetchResponse)#.
    assert isinstance(fetch_resp, DatasetFetchResponse)
    item = fetch_resp.item
    assert isinstance(item, ItemDataset)

    # to turn data time objects to string: yyy-mm-dd
    fetched_metadata = py_to_dict(item.collection_format)

    return fetched_metadata