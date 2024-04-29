import requests
from time import sleep
from typing import Generator, cast
import pytest
import json
from KeycloakRestUtilities.Token import BearerAuth
from ProvenaInterfaces.DataStoreAPI import *
from ProvenaInterfaces.RegistryAPI import DatasetListResponse, ItemSubType, IdentifiedResource, OptionallyRequiredCheck, ItemPerson, ItemOrganisation
from ProvenaInterfaces.RegistryAPI import AccessInfo
from tests.config import config, Tokens
from tests.helpers.datastore_helpers import *
from tests.helpers.general_helpers import py_to_dict
from tests.helpers.link_helpers import *
from resources.example_models import *
from tests.helpers.fixtures import *
from tests.helpers.async_job_helpers import *
from tests.helpers.prov_api_helpers import *
from tests.helpers.release_helpers import *


# system read and write token
token = Tokens.user1


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
        # cleaned up fully
        mint_response = mint_basic_dataset_successfully(
            token=token(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=valid_cf,
                display_name=valid_cf.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri=""),
                release_status=ReleasedStatus.NOT_RELEASED, 
                access_info_uri=valid_cf.dataset_info.access_info.uri,

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

        # Ensure the workflow links were updated
        assert item.workflow_links
        assert item.workflow_links.create_activity_workflow_id

        # wait for the complete lifecycle - step 1
        assert mint_response.register_create_activity_session_id
        create_response = wait_for_full_successful_lifecycle(
            session_id=mint_response.register_create_activity_session_id,
            get_token=Tokens.user1
        )

        assert create_response.result is not None
        parsed_result = RegistryRegisterCreateActivityResult.parse_obj(
            create_response.result)
        lodge_session_id = parsed_result.lodge_session_id
        creation_activity_id = parsed_result.creation_activity_id

        # Clean up dataset Create side effect
        cleanup_items.append(
            (ItemSubType.CREATE, creation_activity_id))

        # Wait for next step of lifecycle - step 2
        # no meaningful response from this - just check success
        wait_for_full_successful_lifecycle(
            session_id=lodge_session_id,
            get_token=Tokens.user1
        )

        # - check the Create activity was produced and is accurate
        fetched_create_activity = cast(ItemCreate, cast(CreateFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.CREATE,
            id=creation_activity_id,
            token=Tokens.user1(),
            model=CreateFetchResponse
        )).item)
        assert fetched_create_activity.created_item_id == item.id

        # - check the prov graph lineage is appropriate

        # The lineage should have item -wasGeneratedBy-> Create activity -
        # wasAssociatedWith -> Person <-wasAttributedTo- Item
        activity_downstream_query = successful_basic_prov_query(
            start=creation_activity_id,
            direction=Direction.DOWNSTREAM,
            depth=1,
            token=Tokens.user1()
        )
        activity_upstream_query = successful_basic_prov_query(
            start=creation_activity_id,
            direction=Direction.UPSTREAM,
            depth=1,
            token=Tokens.user1()
        )
        person_downstream = successful_basic_prov_query(
            start=linked_person_fixture.id,
            direction=Direction.DOWNSTREAM,
            depth=1,
            token=Tokens.user1()
        )

        # 1) Item was generated by registry create
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasGeneratedBy",
                source=item.id,
                target=creation_activity_id
            ),
            lineage_response=activity_downstream_query
        )

        # 2) Item was attributed to Person
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasAttributedTo",
                source=item.id,
                target=linked_person_fixture.id
            ),
            lineage_response=person_downstream
        )

        # 3) Registry Create was associated with Person
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasAssociatedWith",
                source=creation_activity_id,
                target=linked_person_fixture.id
            ),
            lineage_response=activity_upstream_query
        )

        # successful version
        version_response = ds_parsed_version_item(
            id=item.id,
            token=Tokens.user1(),
        )
        revised_item_id = version_response.new_version_id
        cleanup_items.append((item.item_subtype, revised_item_id))
        version_session_id = version_response.version_job_session_id

        # - check new item properties
        fetched_revised_dataset = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.DATASET,
            id=revised_item_id,
            token=Tokens.user1(),
            model=DatasetFetchResponse
        )).item)

        assert fetched_revised_dataset.workflow_links, f"Empty workflow links"
        assert fetched_revised_dataset.workflow_links.version_activity_workflow_id == version_session_id, "Incorrect workflow link"
        assert len(fetched_revised_dataset.history) == 2,\
            f"Inappropriate history length for new version item, len={len(fetched_revised_dataset.history)}"
        v_info = fetched_revised_dataset.versioning_info
        assert v_info, f"Empty versioning info"
        assert int(
            v_info.version) == 2, f"Should be version 2. Was version {v_info.version}"
        assert v_info.previous_version == item.id, f"V2 should refer to V1, referred to {v_info.previous_version}"
        assert v_info.next_version is None, f"V2 should not have a next version yet"

        # - check prev item properties (versioning_info should be updated)
        fetched_original_dataset = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.DATASET,
            id=item.id,
            token=Tokens.user1(),
            model=DatasetFetchResponse
        )).item)

        v_info = fetched_original_dataset.versioning_info
        assert v_info, f"Empty versioning info"
        assert int(
            v_info.version) == 1, f"Should be version 1. Was version {v_info.version}"
        assert v_info.next_version == revised_item_id, f"V1 should refer forward to V2, referred to {v_info.next_version}"
        assert v_info.previous_version is None, f"V1 should not have a previous version"

        # - await async workflow completion

        # wait for the complete lifecycle - step 1
        version_response = wait_for_full_successful_lifecycle(
            session_id=version_session_id,
            get_token=Tokens.user1
        )

        assert version_response.result is not None
        parsed_result = RegistryRegisterVersionActivityResult.parse_obj(
            version_response.result)
        lodge_session_id = parsed_result.lodge_session_id
        version_activity_id = parsed_result.version_activity_id
        cleanup_items.append(
            (ItemSubType.VERSION, version_activity_id))

        # Wait for next step of lifecycle - step 2
        # no meaningful response from this - just check success
        wait_for_full_successful_lifecycle(
            session_id=lodge_session_id,
            get_token=Tokens.user1
        )

        # - check Version properties
        fetched_version_activity = cast(ItemVersion, cast(VersionFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.VERSION,
            id=version_activity_id,
            token=Tokens.user1(),
            model=VersionFetchResponse
        )).item)

        # check the created item is correct
        assert fetched_version_activity.from_item_id == item.id
        assert fetched_version_activity.to_item_id == revised_item_id
        assert int(fetched_version_activity.new_version_number) == 2
        assert fetched_version_activity.owner_username == linked_person_fixture.owner_username

        # - check the prov graph lineage is appropriate

        version_downstream_query = successful_basic_prov_query(
            start=version_activity_id,
            direction=Direction.DOWNSTREAM,
            depth=1,
            token=Tokens.user1()
        )
        version_upstream_query = successful_basic_prov_query(
            start=version_activity_id,
            direction=Direction.UPSTREAM,
            depth=1,
            token=Tokens.user1()
        )
        person_downstream = successful_basic_prov_query(
            start=linked_person_fixture.id,
            direction=Direction.DOWNSTREAM,
            depth=1,
            token=Tokens.user1()
        )

        # 1) New item was generated by registry version
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasGeneratedBy",
                source=revised_item_id,
                target=version_activity_id
            ),
            lineage_response=version_downstream_query
        )

        # 2) New item was attributed to Person
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasAttributedTo",
                source=revised_item_id,
                target=linked_person_fixture.id
            ),
            lineage_response=person_downstream
        )

        # 3) Registry Version was associated with Person
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasAssociatedWith",
                source=version_activity_id,
                target=linked_person_fixture.id
            ),
            lineage_response=version_upstream_query
        )

        # 4) Registry Version used previous version
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="used",
                source=version_activity_id,
                target=item.id
            ),
            lineage_response=version_upstream_query
        )

        # - ensure that cannot produce version from previous item version
        ds_fail_version_item(
            id=item.id,
            expected_code=400,
            token=Tokens.user1()
        )


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

    # cleaned up fully
    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id,
        model=DatasetDomainInfo(
            collection_format=valid_cf,
            display_name=valid_cf.dataset_info.name,
            s3=S3Location(
                bucket_name="", path="", s3_uri=""),
            release_status=ReleasedStatus.NOT_RELEASED,
            access_info_uri=valid_cf.dataset_info.access_info.uri,
        )
    )

    assert mint_response.status.success, f"Mint failed with error: {mint_response.status.details}."
    handle = mint_response.handle
    assert handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, handle))

    cleanup_create_activity_from_dataset_mint(
        mint_response=mint_response,
        get_token=Tokens.user1
    )

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


def test_basic_mint_and_list(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation, dataset_io_fixture: Tuple[str, str]) -> None:
    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture
    id1, id2 = dataset_io_fixture

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
    collection_format.associations.data_custodian_id = person.id

    # use these in the dataset
    # cleaned up fully
    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id,
        model=dataset_domain_info
    )

    assert mint_response.handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, mint_response.handle))

    cleanup_create_activity_from_dataset_mint(
        mint_response=mint_response,
        get_token=Tokens.user1
    )

    # try generate read and write creds and fail
    handle = mint_response.handle

    # this should now succeed
    # NOTE: RRAPIS-1581 changed this behaviour to enable storage access even if externally reposited.
    read_creds_resp = generate_read_creds_successfully(
        dataset_id=handle, token=token())
    write_creds_resp = generate_write_creds_successfully(
        dataset_id=handle, token=token())

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

    read_creds_resp = generate_read_creds_successfully(
        dataset_id=handle, token=token())
    write_creds_resp = generate_write_creds_successfully(
        dataset_id=handle, token=token())


def test_revision_access_backdoor(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation, dataset_io_fixture: Tuple[str, str]) -> None:
    """
    Tests for regression against RRAPIS-1480 

    --- When a dataset is revised, the new version of them item is generated as
    a clone of the previous item. When the data store calls this endpoint, it
    immediately updates the constructed item with the s3 path information of the
    new handle. However, there remains a history entry point for the initial
    state of the item. This bug emerges because the revert operation, exposed
    through the data store, actually allows the user to revert not just the
    collection format subfield, but the entire contents of the dataset. In this
    way, the user can revert to a state where the s3 path points to the previous
    revision, and then subsequently request access to it.

    This update fixes this by changing the dataset revert operation to behave in
    alignment with the update operation. It builds a domain info object based on
    the current state of the item, then overrides only the collection format
    subset of the historical entry, then runs a registry proxy update. ---

    This test runs this sequence and ensures that the S3 path remains after
    revert.

    """

    dataset_id = dataset_io_fixture[0]

    # Now make a revision
    version_response = ds_parsed_version_item(
        id=dataset_id,
        token=Tokens.user1(),
        reason="Testing access regression for versioned item"
    )
    new_ds_id = version_response.new_version_id
    cleanup_items.append((ItemSubType.DATASET, new_ds_id))

    # check the current entry has expected props
    # - check new item properties
    fetched_revised_dataset = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET,
        id=new_ds_id,
        token=Tokens.user1(),
        model=DatasetFetchResponse
    )).item)

    def sanitize(handle: str) -> str:
        return handle.replace('/', '-').replace('.', '-')

    # check the s3 path is at the new location
    sanitized_new_id = sanitize(new_ds_id)
    sanitized_old_id = sanitize(dataset_id)

    assert sanitized_new_id in fetched_revised_dataset.s3.path
    assert sanitized_old_id not in fetched_revised_dataset.s3.path

    # Now revert it
    revert_dataset_successfully(
        dataset_id=new_ds_id,
        history_id=0,
        token=Tokens.user1(),
        reason="Testing security regression for revision revert"
    )

    # fetch again
    fetched_reverted_dataset = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET,
        id=new_ds_id,
        token=Tokens.user1(),
        model=DatasetFetchResponse
    )).item)

    # ensure it still contains the new path
    assert sanitized_new_id in fetched_reverted_dataset.s3.path
    assert sanitized_old_id not in fetched_reverted_dataset.s3.path

    # fetch again
    original_dataset = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET,
        id=dataset_id,
        token=Tokens.user1(),
        model=DatasetFetchResponse
    )).item)

    # ensure it still contains the new path
    assert sanitized_new_id not in original_dataset.s3.path
    assert sanitized_old_id in original_dataset.s3.path

    # Clean up the revision activity
    assert fetched_revised_dataset.workflow_links is not None
    revision_session_id = fetched_revised_dataset.workflow_links.version_activity_workflow_id
    assert revision_session_id is not None

    # wait for the complete lifecycle - step 1
    version_job_response = wait_for_full_successful_lifecycle(
        session_id=revision_session_id,
        get_token=Tokens.user1
    )

    assert version_job_response.result is not None
    parsed_result = RegistryRegisterVersionActivityResult.parse_obj(
        version_job_response.result)
    version_activity_id = parsed_result.version_activity_id
    cleanup_items.append(
        (ItemSubType.VERSION, version_activity_id))


# , dataset_seed_fixture: SeededItem
def test_dataset_release_process(dataset_io_fixture: Tuple[str, str], three_person_tokens_fixture_unlinked_for_release: Tuple[PersonToken, PersonToken, PersonToken]) -> None:

    # 2 datasets created by user1
    dataset_id_1, dataset_id_2 = dataset_io_fixture
    # user1 is first, making them the owner
    owner, reviewer, other_person = three_person_tokens_fixture_unlinked_for_release

    # generate write creds successfuly as not pending/released
    generate_write_creds_successfully(
        dataset_id=dataset_id_1, token=owner.token())

    add_id_to_reviewers_table_and_check(
        token=Tokens.admin(), id=reviewer.id, config=config)

    # acceptable release request with correct approver and not pending/release dataset
    # used to test ownership and user checks
    release_request = ReleaseApprovalRequest(
        dataset_id=dataset_id_1,
        approver_id=reviewer.id,
        notes="Integration Test"
    )

    # hit /approval-request without being linked to a person entity and ensure 400
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=400,
    )

    # now link owner and other person (but not the approver yet as still to test this)
    assign_user_user_assert_success(owner.token(), owner.id)
    assign_user_user_assert_success(other_person.token(), other_person.id)

    # hit /approval-request with a user who is not admin of dataset (but is linked) and ensure 401
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=other_person.token(),
        config=config,
        desired_status_code=401,
    )

    # hit /approval-request using a reviewer who is not a dataset reviewer and ensure 400
    release_request_wrong_reviewer = ReleaseApprovalRequest(
        dataset_id=dataset_id_1,
        approver_id=other_person.id,
        notes="Integration Test using wrong reviewer"
    )
    request_dataset_review_desired_status_code(
        release_approval_request=release_request_wrong_reviewer,
        token=owner.token(),
        config=config,
        desired_status_code=400,
    )

    # Success Case. ensure item is updated currently by re fetching
    # high level fields (release, status, approver and timestamp) and also in the release history fields. (ReleaseHistoryEntry in release_history)
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=200,
    )

    fetch_and_assert_successful_review_request(release_request=release_request, token=owner.token(
    ), expected_released_status=ReleasedStatus.PENDING)

    # hit /approval-request for a dataset that is already pending (now its been requested) and ensure 400
    # (same request again as previous)
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=400,
    )

    # ensure failure to get creds since dataset is pending
    generate_write_creds_assert_status_code(
        dataset_id=dataset_id_1, token=owner.token(), desired_status_code=403)

    # hit /action-approval-request with user who is not linked to a person
    action_request_deny = ActionApprovalRequest(
        dataset_id=dataset_id_1,
        approve=False,
        notes="Integration Test - Rejection!!"
    )

    action_review_request_desired_status_code(
        action_request=action_request_deny,
        token=reviewer.token(),
        config=config,
        desired_status_code=400
    )

    # Now can link to person to check other cases
    assign_user_user_assert_success(reviewer.token(), reviewer.id)
    # hit /action-approval-request as a non dataset reviewer
    remove_id_from_reviewers_table_and_check(
        token=Tokens.admin(), id=reviewer.id, config=config)
    action_review_request_desired_status_code(
        action_request=action_request_deny,
        token=other_person.token(),
        config=config,
        desired_status_code=401
    )
    add_id_to_reviewers_table_and_check(
        token=Tokens.admin(), id=reviewer.id, config=config)

    # hit /action-approval-request and ensure 401 for a user who is a reviewer, but not the reviewer for this dataset
    add_id_to_reviewers_table_and_check(
        token=Tokens.admin(), id=other_person.id, config=config)
    action_review_request_desired_status_code(
        action_request=action_request_deny,
        token=other_person.token(),
        config=config,
        desired_status_code=401
    )

    # hit /action-approval-request and REJECT, check success update of item
    action_review_request_desired_status_code(
        action_request=action_request_deny,
        token=reviewer.token(),
        config=config,
        desired_status_code=200
    )

    fetch_and_assert_successful_action_review_request(
        action_request=action_request_deny, token=owner.token(), expected_released_status=ReleasedStatus.NOT_RELEASED)

    # ensure can make changes to rejected (Release.Status = NOT_RELEASED) dataset
    generate_write_creds_successfully(
        dataset_id=dataset_id_1, token=owner.token())

    # hit /action-approval-request for a dataset that is not pending review (for the one that was just denied)
    action_review_request_desired_status_code(
        action_request=action_request_deny,
        token=reviewer.token(),
        config=config,
        desired_status_code=400
    )

    # hit /action-approval-request for a dataset that is not pending review (a new dataset that hasnt been requested at all)
    action_request_wrong_dataset = ActionApprovalRequest.parse_obj(
        action_request_deny.dict())
    action_request_wrong_dataset.dataset_id = dataset_id_2
    action_review_request_desired_status_code(
        action_request=action_request_wrong_dataset,
        token=reviewer.token(),
        config=config,
        desired_status_code=400
    )

    # re request review successfully, and accept
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=200,
    )

    fetch_and_assert_successful_review_request(release_request=release_request, token=owner.token(
    ), expected_released_status=ReleasedStatus.PENDING)

    action_request_approve = ActionApprovalRequest(
        dataset_id=dataset_id_1,
        approve=True,
        notes="Integration Test - Rejection!!"
    )

    # hit /action-approval-request and ensure correctness. (check high level fields and release history fields)
    action_review_request_desired_status_code(
        action_request=action_request_approve,
        token=reviewer.token(),
        config=config,
        desired_status_code=200
    )

    fetch_and_assert_successful_action_review_request(
        action_request=action_request_approve, token=owner.token(), expected_released_status=ReleasedStatus.RELEASED)

    # hit /approval-request for a dataset that is already released and ensure 400
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=400,
    )

    # ensure cannot generate write creds now it is finally released
    generate_write_creds_assert_status_code(
        dataset_id=dataset_id_1, token=owner.token(), desired_status_code=403)

    # hit /approval-request for a dataset that the reviewer does not have read access and ensure 400
    # remove general registry read and write from dataset
    original_auth_config = get_auth_config(
        id=dataset_id_2, item_subtype=ItemSubType.DATASET, token=owner.token())
    restrictive_auth_config = AccessSettings.parse_obj(
        original_auth_config.dict())
    restrictive_auth_config.general = []
    put_auth_config(id=dataset_id_2, auth_payload=py_to_dict(restrictive_auth_config),
                    item_subtype=ItemSubType.DATASET, token=owner.token())

    release_request = ReleaseApprovalRequest(
        dataset_id=dataset_id_2,
        approver_id=reviewer.id,
        notes="Integration Test"
    )
    # ensure doesnt work because reviewr cant read the dataset!
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=400,
    )

    # allow general user to read
    put_auth_config(id=dataset_id_2, auth_payload=py_to_dict(original_auth_config),
                    item_subtype=ItemSubType.DATASET, token=owner.token())

    # ensure request works now.
    request_dataset_review_desired_status_code(
        release_approval_request=release_request,
        token=owner.token(),
        config=config,
        desired_status_code=200,
    )


def test_presigned_url(dataset_io_fixture: Tuple[str, str]) -> None:

    # Two datasets owned and created by Tokens.user1()
    dataset_id_1, dataset_id_2 = dataset_io_fixture

    # Desire to generate presigned url for metadata.json file in the dataset storage loc.
    url_req = PresignedURLRequest(
        dataset_id=dataset_id_1,
        file_path="metadata.json"
    )

    url_resp = get_presigned_url_successfully(
        pre_signed_url_req=url_req, token=Tokens.user1())

    # check content matches
    downloaded_metadata = fetch_url_content(url_resp.presigned_url)
    fetched_metadata = fetch_dataset_metadata(
        dataset_id=dataset_id_1, token=Tokens.user1())
    assert downloaded_metadata == fetched_metadata, f"Downloaded metadata does not match fetched metadata"

    # give path that does not exist and check fail
    url_req_wrong_path = PresignedURLRequest(
        dataset_id=dataset_id_1,
        file_path="fake_path_123456.json"
    )
    get_presigned_url_status_code(
        pre_signed_url_req=url_req_wrong_path, token=Tokens.user1(), desired_status_code=400)

    # give path that has ../.. and check fail
    url_req_illegal_path = PresignedURLRequest(
        dataset_id=dataset_id_1,
        file_path="../../metadata.json"
    )
    get_presigned_url_status_code(
        pre_signed_url_req=url_req_illegal_path, token=Tokens.user1(), desired_status_code=400)

    # remove dataset read and write check fail (401) (attempt as user 2)
    remove_general_access_from_item(
        id=dataset_id_1, item_subtype=ItemSubType.DATASET, token=Tokens.user1())
    get_presigned_url_successfully(
        pre_signed_url_req=url_req, token=Tokens.user1())  # works for owner
    resp = get_presigned_url_status_code(pre_signed_url_req=url_req, token=Tokens.user2(
    ), desired_status_code=401)  # not for others
    print(resp.text)

    # check with metadata read but not dataset read (401) (attemp at user 2)
    give_general_read_access(
        id=dataset_id_1, item_subtype=ItemSubType.DATASET, token=Tokens.user1())
    resp = get_presigned_url_status_code(
        pre_signed_url_req=url_req, token=Tokens.user2(), desired_status_code=401)
    print(resp.text)

    # give back both metadata and dataset read, check OK
    set_general_access_roles(id=dataset_id_1, general_access_roles=[
                             'metadata-read', 'dataset-data-read'], item_subtype=ItemSubType.DATASET, token=Tokens.user1())
    get_presigned_url_status_code(
        pre_signed_url_req=url_req, token=Tokens.user2(), desired_status_code=200)
    # check content matches
    downloaded_metadata = fetch_url_content(url_resp.presigned_url)
    assert downloaded_metadata == fetched_metadata, f"Downloaded metadata does not match fetched metadata"

    # finally, try for a dataset ID that doesn't exist
    url_req_nonexistant_id = PresignedURLRequest(
        dataset_id="1234234344",
        file_path="metadata.json"
    )
    get_presigned_url_status_code(
        pre_signed_url_req=url_req_nonexistant_id, token=Tokens.user2(), desired_status_code=400)


def test_list_by_access_info_uri(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    # Test for RRAPIS-1545 feature. (Enable fetch/list by URI for non-reposited datasets)

    # person ID linked with 2 users names and admin.
    person = linked_person_fixture
    organisation = organisation_fixture

    dataset_domain_info = cast(DatasetDomainInfo, get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.DATASET))
    collection_format = dataset_domain_info.collection_format
    collection_format.associations.data_custodian_id = person.id

    base_uri = 'https://access_info_uri_example_test.com/'
    access_info_URIs = [
        base_uri + "111",
        base_uri + "122",
        base_uri + "333",
    ]
    handle_uri_map = {}
    uri_handle_map = {}
    for uri in access_info_URIs:
        # register
        collection_format.dataset_info.access_info = AccessInfo(
            reposited=False,
            description="Fake Description",
            uri=uri
        )
        mint_response = mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=dataset_domain_info
        )
        assert mint_response.handle, "Mint response does not contain a handle"
        cleanup_items.append((ItemSubType.DATASET, mint_response.handle))
        cleanup_create_activity_from_dataset_mint(
            mint_response=mint_response, get_token=Tokens.user1)
        
        # keep track for fetching later
        handle_uri_map[mint_response.handle] = uri
        uri_handle_map[uri] = mint_response.handle

    # register one more as reposited
    collection_format.dataset_info.access_info = AccessInfo(reposited=True)
    mint_response = mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=dataset_domain_info
        )
    
    assert mint_response.handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, mint_response.handle))
    cleanup_create_activity_from_dataset_mint(
        mint_response=mint_response, get_token=Tokens.user1)
    basic_id = mint_response.handle
    
    
    # fetch by full URI, ensure only 1 returned and the correct one
    uri = access_info_URIs[0]
    list_resp = list_by_uri_starts_with(uri=uri, token=Tokens.user1())
    assert check_ids_in_list_resp(ids=[uri_handle_map[uri]], list_resp=list_resp), f"List response does not contain the correct handle for URI: {uri}"
    
    # check they all present for the base uri
    list_resp = list_by_uri_starts_with(uri=base_uri, token=Tokens.user1())
    assert check_ids_in_list_resp(ids=list(uri_handle_map.values()), list_resp=list_resp)
    
    uri_begins_with = base_uri + "1"
    list_resp = list_by_uri_starts_with(uri=uri_begins_with, token=Tokens.user1())
    assert check_ids_in_list_resp(ids=[uri_handle_map[uri] for uri in get_starts_withs(uri_begins_with, access_info_URIs)], list_resp=list_resp)
    
    # update_metadata_sucessfully(
    #     dataset_id=handle, updated_metadata=py_to_dict(collection_format), token=token())

    # check that all the other reposited datasets are actually there too.
    list_resp = general_list_exhaust(
        token=Tokens.user1(),
        general_list_request=GeneralListRequest(
            filter_by=FilterOptions(item_subtype=ItemSubType.DATASET),
            )
    )
    assert check_ids_in_list_resp(ids=list(uri_handle_map.values())+[basic_id], list_resp=list_resp)


def test_access_info_uri_field_value_update(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    person = linked_person_fixture
    organisation = organisation_fixture

    dataset_domain_info = cast(DatasetDomainInfo, get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.DATASET))
    collection_format = dataset_domain_info.collection_format
    # make non reposited
    fake_url = "https://fake.url.com"
    collection_format.dataset_info.access_info = AccessInfo(
        reposited=False,
        description="Fake Description",
        uri=fake_url
    )
    collection_format.associations.data_custodian_id = person.id

    # use these in the dataset
    # cleaned up fully
    mint_response = mint_basic_dataset_successfully(
        token=Tokens.user1(),
        author_organisation_id=organisation.id,
        publisher_organisation_id=organisation.id,
        model=dataset_domain_info
    )

    assert mint_response.handle, "Mint response does not contain a handle"
    cleanup_items.append((ItemSubType.DATASET, mint_response.handle))

    cleanup_create_activity_from_dataset_mint(
        mint_response=mint_response,
        get_token=Tokens.user1
    )
    handle = mint_response.handle
    # fetch dataset and check ok
    dataset_item = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.DATASET,
            id=handle,
            token=Tokens.user1(),
            model=DatasetFetchResponse
        )).item)
    assert dataset_item.access_info_uri == dataset_item.collection_format.dataset_info.access_info.uri
    assert dataset_item.access_info_uri == fake_url

    # swap to reposited using update
    collection_format.dataset_info.access_info = AccessInfo(reposited=True)
    update_metadata_sucessfully(
        dataset_id=handle, updated_metadata=py_to_dict(collection_format), token=token())

    dataset_item = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.DATASET,
            id=handle,
            token=Tokens.user1(),
            model=DatasetFetchResponse
        )).item)
    assert dataset_item.access_info_uri == dataset_item.collection_format.dataset_info.access_info.uri, f"Expected {dataset_item.access_info_uri}, got {dataset_item.collection_format.dataset_info.access_info.uri}"
    assert dataset_item.access_info_uri == None, f"Expected None, got {dataset_item.access_info_uri}"

    # swap back
    # swap to reposited using update
    collection_format.dataset_info.access_info = AccessInfo(
        reposited=False,
        description="Fake Description",
        uri=fake_url
    )
    update_metadata_sucessfully(
        dataset_id=handle, updated_metadata=py_to_dict(collection_format), token=token())

    dataset_item = cast(ItemDataset, cast(DatasetFetchResponse, fetch_item_successfully_parse(
            item_subtype=ItemSubType.DATASET,
            id=handle,
            token=Tokens.user1(),
            model=DatasetFetchResponse
        )).item)
    assert dataset_item.access_info_uri == dataset_item.collection_format.dataset_info.access_info.uri, f"Expected {dataset_item.access_info_uri}, got {dataset_item.collection_format.dataset_info.access_info.uri}"
    assert dataset_item.access_info_uri == fake_url, f"Expected {fake_url}, got {dataset_item.access_info_uri}"