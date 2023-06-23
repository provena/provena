import requests
from time import sleep
from typing import Generator, cast
import pytest
import json
from KeycloakRestUtilities.Token import BearerAuth
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryAPI import DatasetListResponse, ItemSubType, IdentifiedResource, OptionallyRequiredCheck, ItemPerson, ItemOrganisation
from SharedInterfaces.RegistryAPI import AccessInfo
from tests.config import config, Tokens
from tests.helpers.datastore_helpers import *
from tests.helpers.registry_helpers import perform_entity_cleanup, create_item_successfully
from tests.helpers.general_helpers import py_to_dict
from tests.helpers.link_helpers import *
from resources.example_models import *


# system read and write token
token = Tokens.user1
cleanup_items: List[Tuple[ItemSubType, IdentifiedResource]] = []

# fixture to clean up items


@pytest.fixture(scope='session', autouse=False)
def person_fixture() -> Generator[ItemPerson, None, None]:
    # create person 1 and 2  (user 1 and 2)
    person = create_item_successfully(
        item_subtype=ItemSubType.PERSON,
        token=Tokens.user1()
    )

    # provide to any test that uses them
    yield cast(ItemPerson, person)

    # clean up
    perform_entity_cleanup([
        (person.item_subtype, person.id),
    ], token=Tokens.admin())


@pytest.fixture(scope='session', autouse=False)
def linked_person_fixture(person_fixture: ItemPerson) -> Generator[ItemPerson, None, None]:
    person = person_fixture

    # link this person to person1, person2 and admin - need to perform as admin
    # to overcome ownership issue
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user1_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.user2_username, force=True)
    assign_user_admin_assert_success(token=Tokens.admin(
    ), person_id=person.id, username=Tokens.admin_username, force=True)

    # provide to any test that uses them
    yield person

    # clean up links
    perform_link_cleanup([
        Tokens.user1_username,
        Tokens.user2_username,
        Tokens.admin_username,
    ], token=Tokens.admin())


@pytest.fixture(scope='session', autouse=False)
def organisation_fixture() -> Generator[ItemOrganisation, None, None]:
    # create person 1 and 2  (user 1 and 2)
    org = create_item_successfully(
        item_subtype=ItemSubType.ORGANISATION,
        token=Tokens.user1()
    )

    # provide to any test that uses them
    yield cast(ItemOrganisation, org)

    # clean up
    perform_entity_cleanup([
        (org.item_subtype, org.id),
    ], token=Tokens.admin())


@pytest.fixture(scope='session', autouse=True)
def entity_cleanup_fixture() -> Generator:
    yield
    perform_entity_cleanup(cleanup_items, token=Tokens.admin())


def test_integration_fetch_invalid_dataset() -> None:
    params = {
        "handle_id": config.INVALID_HANDLE
    }

    response = requests.get(
        config.DATA_STORE_API_ENDPOINT + "/registry/items/fetch-dataset",
        auth=BearerAuth(token()),
        params=params,
    )

    assert response.status_code == 400, f'Status code is not 400, response message: {response.text}'


def test_integration_mint_and_fetch(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture

    # check we are linked
    lookup_user_user_assert_success(token=Tokens.user1(), check_id=person.id)

    # models to test
    valid_collection_formats: List[CollectionFormat] = [
        valid_collection_format1,
        valid_collection_format2
    ]

    for valid_cf in valid_collection_formats:
        mint_response = mint_basic_dataset_successfully(
            token=token(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=valid_cf,
                display_name=valid_cf.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri="")
            )
        )

        assert mint_response.status.success, "Reported failure when minting"
        assert mint_response.handle, "Mint response does not contain a handle"
        cleanup_items.append((ItemSubType.DATASET, mint_response.handle))
        params = {
            'handle_id': mint_response.handle
        }
        response = requests.get(
            config.DATA_STORE_API_ENDPOINT + "/registry/items/fetch-dataset",
            params=params,
            auth=BearerAuth(token())
        )
        assert response.status_code == 200, f'Status code is not 200, response message: {response.text}'
        registry_fetch_response = RegistryFetchResponse.parse_obj(
            response.json())
        item = registry_fetch_response.item
        # Check equality as required
        assert item, "Item is empty"
        assert item.id == mint_response.handle, "Fetched item id does not match mint response handle"
        assert item.collection_format.dataset_info.description == valid_cf.dataset_info.description, "Fetched item description does not match original metadata"


def post_update_for_validation(handle: str, success: bool, collection_format: CollectionFormat) -> None:
    # provide a reason for the update
    reason = "Integration testing"
    response = requests.post(
        config.DATA_STORE_API_ENDPOINT + '/register/update-metadata',
        params={'handle_id': handle, 'reason': reason},
        json=py_to_dict(collection_format),
        auth=BearerAuth(token()),
    )

    if success:
        assert response.status_code == 200, f"Status code is not 200, response message: {response.text}"
        update_metadata_response = UpdateMetadataResponse.parse_obj(
            response.json())
        assert update_metadata_response.status.success, f"Update metadata failed with error: {update_metadata_response.status.details}."
    else:
        assert response.status_code == 400, f"Status code is not 400, response message: {response.text}"


def validate_optional_check_behaviour(handle: str, field: OptionallyRequiredCheck, data: CollectionFormat) -> None:
    # make sure it doesn't change value
    initial_relevant = field.relevant
    initial_obtained = field.obtained

    # Test: consent obtained but not relevant (fail)
    field.relevant = False
    field.obtained = True
    post_update_for_validation(
        handle=handle, collection_format=data, success=False)

    # Test: consent not obtained but relevant (fail)
    field.relevant = True
    field.obtained = False
    post_update_for_validation(
        handle=handle, collection_format=data, success=False)

    # Test: consent obtained and relevant (succeed)
    field.relevant = True
    field.obtained = True
    post_update_for_validation(
        handle=handle, collection_format=data, success=True)

    # Test: consent not obtained and not relevant (succeed)
    field.relevant = False
    field.obtained = False
    post_update_for_validation(
        handle=handle, collection_format=data, success=True)

    field.relevant = initial_relevant
    field.obtained = initial_obtained


def test_mint_and_update_metadata(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    """    
    Aims to test whether the update-metadata api is working correctly by:

    1. minting a dataset with an original metadata file
    2. confirming this mint and fetching metadata to make sure it matches the inputted original metadata
    3. updating the metadata using a different file to replace the current metadata
    4. Fetching the metadata and checking it matches the file used to update it with
    """

    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture

    # check we are linked
    lookup_user_user_assert_success(token=Tokens.user1(), check_id=person.id)

    # model to test
    valid_cf = valid_collection_format1

    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id,
        model=DatasetDomainInfo(
            collection_format=valid_cf,
            display_name=valid_cf.dataset_info.name,
            s3=S3Location(
                bucket_name="", path="", s3_uri="")
        )
    )

    assert mint_response.status.success, f"Mint failed with error: {mint_response.status.details}."
    handle = mint_response.handle
    assert handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, handle))
    response = requests.get(
        config.DATA_STORE_API_ENDPOINT + "/registry/items/fetch-dataset",
        params={'handle_id': handle},
        auth=BearerAuth(token()),
    )
    assert response.status_code == 200, f"Status code is not 200, response message: {response.text}"
    fetch_response = RegistryFetchResponse.parse_obj(response.json())
    assert fetch_response.item, "Item is empty"
    fetched_metadata = fetch_response.item.collection_format
    parsed_fetched_metadata = json.loads(
        fetched_metadata.json(exclude_none=True))
    assert py_to_dict(
        valid_cf) == parsed_fetched_metadata, "Fetched item does not match original metadata"
    original_created_time = fetch_response.item.created_timestamp
    original_updated_time = fetch_response.item.updated_timestamp

    # wait for a second to make sure the updated timestamp is distinct
    sleep(1)

    # now update - ensure the IDs are accurate
    valid_cf = valid_collection_format3
    valid_cf.associations.organisation_id = organisation.id
    valid_cf.dataset_info.publisher_id = organisation.id

    # provide a reason for the update
    reason = "Integration testing"
    response = requests.post(
        config.DATA_STORE_API_ENDPOINT + '/register/update-metadata',
        params={'handle_id': handle, 'reason': reason},
        json=py_to_dict(valid_cf),
        auth=BearerAuth(token()),
    )
    assert response.status_code == 200, f"Status code is not 200, response message: {response.text}"

    update_metadata_response = UpdateMetadataResponse.parse_obj(
        response.json())
    assert update_metadata_response.status.success, f"Update metadata failed with error: {update_metadata_response.status.details}."

    response = requests.get(
        config.DATA_STORE_API_ENDPOINT + "/registry/items/fetch-dataset",
        params={'handle_id': handle},
        auth=BearerAuth(token()),
    )

    assert response.status_code == 200, f"Status code is not 200, response message: {response.text}"
    fetch_response = RegistryFetchResponse.parse_obj(response.json())
    assert fetch_response.status.success, f"Fetch failed with error: {fetch_response.status.details}."
    assert fetch_response.item, "Item is empty"
    fetched_metadata_updated = fetch_response.item.collection_format
    parsed_fetched_metadata = json.loads(
        fetched_metadata_updated.json(exclude_none=True))
    assert py_to_dict(
        valid_cf) == parsed_fetched_metadata, "Fetched item does not match updated metadata"
    new_created_time = fetch_response.item.created_timestamp
    new_updated_time = fetch_response.item.updated_timestamp
    assert new_created_time == original_created_time, "Created timestamp has changed"
    assert new_updated_time > original_updated_time, "Updated timestamp has not changed"

    # now test that updating is only successful in valid combinations of optional checks (ethics, indigenous, export controls)
    assert handle
    collection_format = CollectionFormat.parse_obj(py_to_dict(valid_cf))

    # test for each of the optional check fields to ensure behaviour is consistent
    fields: List[OptionallyRequiredCheck] = [
        collection_format.approvals.ethics_access,
        collection_format.approvals.ethics_registration,
        collection_format.approvals.export_controls,
        collection_format.approvals.indigenous_knowledge,
    ]
    for f in fields:
        # ethics access
        validate_optional_check_behaviour(
            field=f,
            handle=handle,
            data=collection_format,
        )


def test_basic_mint_and_list(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture

    # use these in the dataset
    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id
    )

    assert mint_response.handle
    cleanup_items.append((ItemSubType.DATASET, mint_response.handle))

    response = requests.post(
        config.DATA_STORE_API_ENDPOINT + "/registry/items/list",
        json={},
        auth=BearerAuth(token()),
    )
    assert response.status_code == 200, f'Status code is not 200, response message: {response.text}'
    list_registry_response = DatasetListResponse.parse_obj(response.json())
    assert list_registry_response.status.success, f'List failed with error: {list_registry_response.status.details}.'
    assert list_registry_response.items, "List response does not contain any items"
    assert len(
        list_registry_response.items) > 0, "List response does not contain any items"


def test_non_reposited_download_and_upload(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    person = linked_person_fixture
    organisation = organisation_fixture

    dataset_domain_info = cast(DatasetDomainInfo, get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.DATASET))
    collection_format = dataset_domain_info.collection_format
    # make non reposited
    collection_format.dataset_info.access_info = AccessInfo(
        reposited=False,
        description="Fake Description",
        uri="https://fake.url.com"
    )

    # use these in the dataset
    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id,
        model=dataset_domain_info
    )

    assert mint_response.handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, mint_response.handle))

    # try generate read and write creds and fail
    handle = mint_response.handle

    read_creds_resp = generate_read_creds(dataset_id=handle, token=token())
    assert read_creds_resp.status_code == 400, f"Status code is not 400, response message: {read_creds_resp.text}"
    write_creds_resp = generate_write_creds(dataset_id=handle, token=token())
    assert write_creds_resp.status_code == 400, f"Status code is not 400, response message: {write_creds_resp.text}"

    # swap to reposited using update
    collection_format.dataset_info.access_info = AccessInfo(reposited=True)
    update_metadata_sucessfully(
        dataset_id=handle, updated_metadata=py_to_dict(collection_format), token=token())

    # try generate read and write creds and succeed
    read_creds_resp = generate_read_creds_successfully(
        dataset_id=handle, token=token())
    write_creds_resp = generate_write_creds_successfully(
        dataset_id=handle, token=token())

    # swap back
    # swap to reposited using update
    collection_format.dataset_info.access_info = AccessInfo(
        reposited=False,
        description="Fake Description",
        uri="https://fake.url.com"
    )
    update_metadata_sucessfully(
        dataset_id=handle, updated_metadata=py_to_dict(collection_format), token=token())

    resp = generate_read_creds(dataset_id=handle, token=token())
    assert resp.status_code == 400, f"Status code is not 400, response message: {resp.text}"
    resp = generate_write_creds(dataset_id=handle, token=token())
    assert resp.status_code == 400, f"Status code is not 400, response message: {resp.text}"
