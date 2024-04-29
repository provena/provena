import requests
from KeycloakRestUtilities.Token import BearerAuth
from ProvenaInterfaces.RegistryAPI import *
from tests.helpers.registry_helpers import *
from tests.helpers.auth_helpers import *
from tests.config import Tokens, config
from tests.helpers.link_helpers import *
from resources.example_models import *
from typing import cast
from tests.helpers.async_job_helpers import *
from ProvenaInterfaces.AsyncJobModels import *
from tests.helpers.fixtures import *
from tests.helpers.prov_api_helpers import *

def test_integration_list_all() -> None:
    list_endpoint = config.REGISTRY_API_ENDPOINT + "/registry/general/list"
    response = requests.post(list_endpoint,
                             auth=BearerAuth(Tokens.user1()),
                             json={}  # currently expects a payload even if it's empty
                             )
    assert response.status_code == 200, f'Status code is not 200, response message: {response.text}'
    list_registry_response = GenericListResponse.parse_obj(response.json())
    assert list_registry_response.status.success


def test_item_auth_and_edit_workflow(group_cleanup_fixture: None) -> None:
    # create an item as user1 and remove access from it
    # try to read item as user2 - ensure fail
    # create a group with user 2 and add group to item auth config to read
    # try to read again as user 2 and ensure success
    # try to write to item as user2 and ensure failure
    # create new group with user2 in it and give that group write access to item
    # ensure users2 can now write
    # fetch teh auth and ensure both groups are there
    # lock item
    # try update and ensure failure
    # check lock status
    # unlock item and ensure can edit again
    # fetch item and ensure it was updated.

    org_domain_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.ORGANISATION)
    org1 = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1(),
        domain_info=org_domain_info)
    cleanup_items.append((org1.item_subtype, org1.id))

    remove_general_access_from_item(
        id=org1.id,
        item_subtype=org1.item_subtype,
        token=Tokens.user1()
    )

    # try fetch item as user2 and ensure failure due to restricted general access
    fetch_resp = fetch_item(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user2())
    assert fetch_resp.status_code == 401, f"Expected 401 to signify expected failed fetch due to access rights. Got {fetch_resp.status_code} instead."

    # create group (using admin token as this is admin only endpoint)
    test_group_id = 'registry_integration_test_group_read_only'
    group_metadata = {
        "id": test_group_id,
        "display_name": "registry integration test group read only",
        "description": "A test group for registry api integration tests (read only)",
    }
    # add to cleanup before attempting to add
    cleanup_group_ids.append(test_group_id)
    add_group_resp = add_group_successfully(
        group_metadata=group_metadata, token=Tokens.admin())

    # Create group user obj for second user and add them to read only group
    group_user2 = GroupUser(
        username=config.SYSTEM_WRITE_USERNAME_2,
        email="fakeEmail111@gmail.com",
        first_name="Steve",
        last_name="CoralLover"
    )
    add_member_resp = add_member_to_group_successfully(
        user=group_user2, group_id=test_group_id, token=Tokens.admin())

    # now actually set the read only group to be able to read the item
    org1_group_roles = {
        test_group_id: ['metadata-read']
    }
    set_group_access_roles(id=org1.id, item_subtype=ItemSubType.ORGANISATION,
                           group_access_roles=org1_group_roles, token=Tokens.user1())

    # now try fetch item with user2 in the group
    fetch_resp = fetch_item_successfully(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user2())

    # try update item as user2 and fail
    org_domain_info.display_name = org_domain_info.display_name + " Verion 2.0"
    update_resp = update_item(
        id=org1.id,
        token=Tokens.user2(),
        item_subtype=ItemSubType.ORGANISATION,
        updated_domain_info=org_domain_info
    )
    assert update_resp.status_code == 401, f"Expected 401 to signify expected failed update due to access rights. Got {update_resp.status_code} instead."

    # add another group that has write access and add user2 and then try update again.
    write_test_group_id = 'other registry integration test group for write access'
    group2_metadata = {
        "id": write_test_group_id,
        "display_name": "Secondary registry integration test group to give write access",
        "description": "A test group for registry api integration tests (to have write access)",
    }
    cleanup_group_ids.append(write_test_group_id)

    add_group_resp = add_group_successfully(
        group_metadata=group2_metadata, token=Tokens.admin())
    add_member_resp = add_member_to_group_successfully(
        user=group_user2, group_id=write_test_group_id, token=Tokens.admin())

    org1_group_roles = {
        write_test_group_id: ['metadata-write']
    }
    # add roles for write group to the item
    add_group_access_roles(id=org1.id, item_subtype=ItemSubType.ORGANISATION,
                           group_access_roles=org1_group_roles, token=Tokens.user1())

    # now should be able to update with user2
    update_resp = update_item(
        id=org1.id,
        token=Tokens.user2(),
        item_subtype=ItemSubType.ORGANISATION,
        updated_domain_info=org_domain_info
    )
    assert update_resp.status_code == 200, f"Expected 200 to signify successful update. Got {update_resp.status_code} instead."

    # fetch auth and ensure both groups are there
    auth_config = get_auth_config(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1())
    assert auth_config.groups == {
        test_group_id: ['metadata-read'],
        write_test_group_id: ['metadata-write'],
    }, f"Expected auth config to have both groups. Got {auth_config.groups} instead."

    # lock item
    lock_resp = lock_item(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1())
    # try to update as owner and ensure failure
    org_domain_info.display_name = org_domain_info.display_name + " Verion 3.0"
    update_resp = update_item(
        id=org1.id,
        token=Tokens.user2(),
        item_subtype=ItemSubType.ORGANISATION,
        updated_domain_info=org_domain_info
    )
    assert update_resp.status_code == 401, f"Expected 'invalid access 401', recieved {update_resp.status_code}."
    # unlock item

    # fetch lock status and ensure locked
    lock_status = get_lock_status(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1())
    assert lock_status.locked, f"Expected lock status to be locked. Got {lock_status.locked} instead."

    unlock_resp = unlock_item(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1())
    # fetch lock status and ensure unlocked
    lock_status = get_lock_status(
        id=org1.id, item_subtype=ItemSubType.ORGANISATION, token=Tokens.user1())
    assert not lock_status.locked, f"Expected lock status to be unlocked. Got {lock_status.locked} instead."

    # try to update again and succeed
    update_resp = update_item(
        id=org1.id,
        token=Tokens.user2(),
        item_subtype=ItemSubType.ORGANISATION,
        updated_domain_info=org_domain_info
    )
    assert update_resp.status_code == 200, f"Expected 200, recieved {update_resp.status_code}."

    # fetch item and ensure it actually updated.
    fetch_resp = fetch_item_successfully(
        item_subtype=ItemSubType.ORGANISATION, id=org1.id, token=Tokens.user1())
    fetched_org = fetch_resp.item
    assert isinstance(
        fetched_org, ItemBase), f"Expected fetched item to be of type ItemBase. Got {type(fetched_org)} instead."
    assert fetched_org.display_name == org_domain_info.display_name, f"Expected fetched item to have updated display name. Got {fetched_org.display_name} instead."


def test_list(linked_person_fixture: ItemPerson) -> None:
    # make some models
    # make some orgs
    # test filtering and ordering

    model_dom_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.MODEL)
    org_dom_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.ORGANISATION)

    num_per_type = 3
    for _ in range(num_per_type):
        # make them together in a loop to get a mix when ordering my created time.
        model_item = create_item_from_domain_info_successfully(
            item_subtype=ItemSubType.MODEL,
            token=Tokens.user1(),
            domain_info=model_dom_info
        )
        cleanup_items.append((ItemSubType.MODEL, model_item.id))
        
        # cleanup model create activities
        cleanup_create_activity_from_item_base(item=model_item, get_token=Tokens.user1)

        org_item = create_item_from_domain_info_successfully(
            item_subtype=ItemSubType.ORGANISATION,
            token=Tokens.user1(),
            domain_info=org_dom_info
        )
        cleanup_items.append((ItemSubType.ORGANISATION, org_item.id))

    # get all
    listed_models = general_list_first_n(
        token=Tokens.user1(),
        first_num=3,
        general_list_request=GeneralListRequest(
            filter_by=FilterOptions(
                item_subtype=ItemSubType.MODEL,
            ),
            sort_by=SortOptions(
                sort_type=SortType.CREATED_TIME,
                ascending=False  # most recent first
            )
        )
    )
    listed_models = [ItemBase.parse_obj(model) for model in listed_models]
    check_item_created_timestamp_sorting_and_type(
        items=listed_models, ascending=False, subtype=ItemSubType.MODEL)

    listed_orgs = general_list_first_n(
        token=Tokens.user1(),
        first_num=3,
        general_list_request=GeneralListRequest(
            filter_by=FilterOptions(
                item_subtype=ItemSubType.ORGANISATION,
            ),
            sort_by=SortOptions(
                sort_type=SortType.CREATED_TIME,
                ascending=False  # most recent first
            )
        )
    )
    listed_orgs = [ItemBase.parse_obj(org) for org in listed_orgs]
    check_item_created_timestamp_sorting_and_type(
        items=listed_orgs, ascending=False, subtype=ItemSubType.ORGANISATION)

    # now try reverse the order
    listed_orgs = general_list_first_n(
        token=Tokens.user1(),
        first_num=3,
        general_list_request=GeneralListRequest(
            sort_by=SortOptions(
                sort_type=SortType.CREATED_TIME,
                ascending=True  # most oldest first
            )
        )
    )
    listed_orgs = [ItemBase.parse_obj(org) for org in listed_orgs]
    check_item_created_timestamp_sorting_and_type(
        items=listed_orgs, ascending=True)


def test_person_ethics_approved_validation() -> None:
    # get person domain info
    person_domain_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.PERSON)
    # make a copy so we are not altering the example directly so it can be used in other tests as is
    person_domain_info = PersonDomainInfo.parse_obj(person_domain_info.dict())

    # create person successfully
    person_item = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.PERSON, token=Tokens.user1(), domain_info=person_domain_info)
    cleanup_items.append((ItemSubType.PERSON, person_item.id))
    # fetch person and ensure it is ethics approved
    person_item = fetch_complete_person_item_successfully(
        id=person_item.id, token=Tokens.user1())
    assert person_item.ethics_approved, f"Expected fetched item to have ethics approved. Got {person_item.ethics_approved} instead."

    # update person to not be ethics approved
    person_domain_info.ethics_approved = False
    update_resp = update_item(
        id=person_item.id,
        token=Tokens.user1(),
        item_subtype=ItemSubType.PERSON,
        updated_domain_info=person_domain_info
    )
    # check status 200 but with error in response
    assert update_resp.status_code == 200, f"Expected 200, recieved {update_resp.status_code}."
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, f"Expected update to fail. Got {update_resp.status.success} instead."

    # fetch person and ensure it is still ethics approved
    person_item = fetch_complete_person_item_successfully(
        id=person_item.id, token=Tokens.user1())
    assert person_item.ethics_approved, f"Expected fetched item to have ethics approved. Got {person_item.ethics_approved} instead."

    # try create person without ethics approved and ensure failure
    person_domain_info.ethics_approved = False
    create_resp = create_item_from_domain_info(
        item_subtype=ItemSubType.PERSON, token=Tokens.user1(), domain_info=person_domain_info)
    # check status 200 but with error in response
    assert create_resp.status_code == 200, f"Expected 200, recieved {create_resp.status_code}."
    create_resp = StatusResponse.parse_obj(create_resp.json())
    assert not create_resp.status.success, f"Expected create to fail due to no ethics approval. Got {create_resp.status.success} instead."


def test_invalid_mrwt_update(linked_person_fixture: ItemPerson) -> None:
    # Test that will create the requirements needed for a MRWT register it succesfully, then,
    # will try to update the MRWT with invalid handle references and ensure failure
    # register custom dataset templates (input and output)
    input_deferred_resource_key = "key1"
    input_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=Tokens.user1(),
        domain_info=DatasetTemplateDomainInfo(
            description="A template for integration Test input dataset",
            display_name="Integration test input template",
            defined_resources=[
                DefinedResource(
                    usage_type=ResourceUsageType.GENERAL_DATA,
                    description="Used for connectivities",
                    path="forcing/",
                )
            ],
            deferred_resources=[
                DeferredResource(
                    usage_type=ResourceUsageType.GENERAL_DATA,
                    description="Used for connectivities",
                    key=input_deferred_resource_key,
                )
            ]
        )
    )
    cleanup_items.append((input_template.item_subtype, input_template.id))

    # Cleanup registry create
    cleanup_create_activity_from_item_base(
        item=input_template,
        get_token=Tokens.user1
    )

    output_deferred_resource_key = "Key2"
    output_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=Tokens.user1(),
        domain_info=DatasetTemplateDomainInfo(
            description="A template for integration Test output dataset",
            display_name="Integration test output template",
            defined_resources=[
                DefinedResource(
                    usage_type=ResourceUsageType.GENERAL_DATA,
                    description="Used for connectivities",
                    path="forcing/",
                )
            ],
            deferred_resources=[
                DeferredResource(
                    usage_type=ResourceUsageType.GENERAL_DATA,
                    description="Used for connectivities",
                    key=output_deferred_resource_key,
                )
            ]
        )
    )
    cleanup_items.append((output_template.item_subtype, output_template.id))
    
    # Cleanup registry create
    cleanup_create_activity_from_item_base(
        item=output_template,
        get_token=Tokens.user1
    )

    # regiter the model used in the model run
    model = create_item_successfully(
        item_subtype=ItemSubType.MODEL, token=Tokens.user1())
    cleanup_items.append((model.item_subtype, model.id))
    
    
    # Cleanup registry create
    cleanup_create_activity_from_item_base(
        item=model,
        get_token=Tokens.user1
    )

    # create and register model run workflow template
    required_annotation_key = "annotation_key1"
    optional_annotation_key = "annotation_key2"
    mrwt_domain_info = ModelRunWorkflowTemplateDomainInfo(
        display_name="IntegrationTestMRWT",
        software_id=model.id,  # model is software
        input_templates=[TemplateResource(
            template_id=input_template.id, optional=False)],
        output_templates=[TemplateResource(
            template_id=output_template.id, optional=False)],
        annotations=WorkflowTemplateAnnotations(
            required=[required_annotation_key],
            optional=[optional_annotation_key]
        )
    )
    mrwt = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE, token=Tokens.user1(), domain_info=mrwt_domain_info)
    cleanup_items.append((mrwt.item_subtype, mrwt.id))
    
    
    # Cleanup registry create
    cleanup_create_activity_from_item_base(
        item=mrwt,
        get_token=Tokens.user1
    )

    # update mrwt domain info with invalid handles one by one and test ensure failure to validate by checking 200 but failure in status.

    # make invalid software id and ensure exception
    mrwt_domain_info.software_id = "invalid_software_id"
    update_resp = update_item(id=mrwt.id, token=Tokens.user1(), updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid software id but got success"

    # make invalid input template id and ensure exception
    mrwt_domain_info.software_id = model.id
    mrwt_domain_info.input_templates[0].template_id = "invalid_input_template_id"
    update_resp = update_item(id=mrwt.id, token=Tokens.user1(), updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid input template id but got success"

    # make invalid output template id and ensure exception
    mrwt_domain_info.input_templates[0].template_id = input_template.id
    mrwt_domain_info.output_templates[0].template_id = "invalid_output_template_id"
    update_resp = update_item(id=mrwt.id, token=Tokens.user1(), updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid output template id but got success"


def test_create_and_version_async_workflow(linked_person_fixture: ItemPerson) -> None:
    """
    CREATE
    - create a dataset template
    - await the async workflow completion
    - check the Create activity was produced and is accurate
    - check the prov graph lineage is appropriate 
    VERSION 
    - produce version from existing item
    - await async workflow completion 
    - check new item properties
    - check Version properties
    - check prov lineage
    - update item making no domain changes and check all non-changing properties persist
    - ensure that cannot produce version from previous item version
    - produce another version and perform same monitoring
    """

    # CREATE
    # - create a dataset template

    first_template_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.DATASET_TEMPLATE
    )
    # cleaned up
    first_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        domain_info=first_template_info,
        token=Tokens.user1()
    )
    cleanup_items.append((first_template.item_subtype, first_template.id))


    # - await the async workflow completion
    assert first_template.workflow_links is not None, f"Expected item payload to include create workflow link"
    create_session_id = first_template.workflow_links.create_activity_workflow_id
    assert create_session_id is not None, f"Expected item payload to include create workflow link"

    # wait for the complete lifecycle - step 1
    create_response = wait_for_full_successful_lifecycle(
        session_id=create_session_id,
        get_token=Tokens.user1
    )

    assert create_response.result is not None
    parsed_result = RegistryRegisterCreateActivityResult.parse_obj(
        create_response.result)
    lodge_session_id = parsed_result.lodge_session_id
    creation_activity_id = parsed_result.creation_activity_id
    cleanup_items.append((ItemSubType.CREATE, creation_activity_id))

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

    # check the created item is correct
    assert fetched_create_activity.created_item_id == first_template.id

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

    # Check for presence of each link

    # 1) Item was generated by registry create
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasGeneratedBy",
            source=first_template.id,
            target=creation_activity_id
        ),
        lineage_response=activity_downstream_query
    )

    # 2) Item was attributed to Person
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasAttributedTo",
            source=first_template.id,
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

    # VERSION
    # - produce version from existing item

    # successful version
    explicit_reason = "This is a reason for versioning"
    version_response = parsed_version_item(
        id=first_template.id,
        token=Tokens.user1(),
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        reason=explicit_reason
    )
    revised_item_id = version_response.new_version_id
    cleanup_items.append((first_template.item_subtype, revised_item_id))
    version_session_id = version_response.version_job_session_id

    # - check new item properties
    fetched_revised_template = cast(ItemDatasetTemplate, cast(DatasetTemplateFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        id=revised_item_id,
        token=Tokens.user1(),
        model=DatasetTemplateFetchResponse
    )).item)

    assert fetched_revised_template.workflow_links, f"Empty workflow links"
    assert fetched_revised_template.workflow_links.version_activity_workflow_id == version_session_id, "Incorrect workflow link"
    assert len(fetched_revised_template.history) == 1,\
        f"Inappropriate history length for new version item, len={len(fetched_revised_template.history)}"
    v_info = fetched_revised_template.versioning_info
    assert v_info, f"Empty versioning info"
    assert int(
        v_info.version) == 2, f"Should be version 2. Was version {v_info.version}"
    assert v_info.previous_version == first_template.id, f"V2 should refer to V1, referred to {v_info.previous_version}"
    assert v_info.next_version is None, f"V2 should not have a next version yet"
    assert v_info.reason is not None
    assert v_info.reason == explicit_reason, f"Reason was not in versioning info, expected {explicit_reason} got {v_info.reason}"

    # - check prev item properties (versioning_info should be updated)
    fetched_original_template = cast(ItemDatasetTemplate, cast(DatasetTemplateFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        id=first_template.id,
        token=Tokens.user1(),
        model=DatasetTemplateFetchResponse
    )).item)

    v_info = fetched_original_template.versioning_info
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
    cleanup_items.append((ItemSubType.VERSION, version_activity_id))

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
    assert fetched_version_activity.from_item_id == first_template.id
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
            target=first_template.id
        ),
        lineage_response=version_upstream_query
    )

    # - update item making no domain changes and check all non-changing properties persist
    parsed_successful_update_item(
        id=revised_item_id,
        # same info
        updated_domain_info=first_template_info,
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=Tokens.user1()
    )

    updated_fetched_revised_template = cast(ItemDatasetTemplate, cast(DatasetTemplateFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        id=revised_item_id,
        token=Tokens.user1(),
        model=DatasetTemplateFetchResponse
    )).item)

    # exclude changing properties
    excluded_props = ['updated_timestamp', 'history']

    def remove_props(model: BaseModel) -> Dict[str, Any]:
        new_dict = py_to_dict(model)
        for prop in excluded_props:
            del new_dict[prop]
        return new_dict

    # compare pre vs post update
    orig = remove_props(fetched_revised_template)
    new = remove_props(updated_fetched_revised_template)
    assert orig == new

    # - ensure that cannot produce version from previous item version
    fail_version_item(
        id=first_template.id,
        expected_code=400,
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=Tokens.user1()
    )

    # - produce another version and perform same test

    # successful version
    version_req_response = parsed_version_item(
        id=revised_item_id,
        token=Tokens.user1(),
        item_subtype=ItemSubType.DATASET_TEMPLATE
    )
    second_revised_item_id = version_req_response.new_version_id
    cleanup_items.append((first_template.item_subtype, second_revised_item_id))
    version_session_id = version_req_response.version_job_session_id

    # - check new item properties
    fetched_revised_template = cast(ItemDatasetTemplate, cast(DatasetTemplateFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        id=second_revised_item_id,
        token=Tokens.user1(),
        model=DatasetTemplateFetchResponse
    )).item)

    assert fetched_revised_template.workflow_links, f"Empty workflow links"
    assert fetched_revised_template.workflow_links.version_activity_workflow_id == version_session_id, "Incorrect workflow link"
    assert len(fetched_revised_template.history) == 1,\
        f"Inappropriate history length for new version item, len={len(fetched_revised_template.history)}"
    v_info = fetched_revised_template.versioning_info
    assert v_info, f"Empty versioning info"
    assert int(
        v_info.version) == 3, f"Should be version 3. Was version {v_info.version}"
    assert v_info.previous_version == revised_item_id, f"V3 should refer to V2, referred to {v_info.previous_version}"
    assert v_info.next_version is None, f"V3 should not have a next version"

    # - fetch middle version - check back and forward references
    fetched_middle_template = cast(ItemDatasetTemplate, cast(DatasetTemplateFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        id=revised_item_id,
        token=Tokens.user1(),
        model=DatasetTemplateFetchResponse
    )).item)

    v_info = fetched_middle_template.versioning_info
    assert v_info, f"Empty versioning info"
    assert int(
        v_info.version) == 2, f"Should be version 2. Was version {v_info.version}"
    assert v_info.next_version == second_revised_item_id, f"V2 should refer forward to V3, referred to {v_info.next_version}"
    assert v_info.previous_version == first_template.id, f"V2 should refer back to V1, referred to {v_info.previous_version}"

    # - await async workflow completion

    # wait for the complete lifecycle - step 1
    create_response = wait_for_full_successful_lifecycle(
        session_id=version_session_id,
        get_token=Tokens.user1
    )

    assert create_response.result is not None
    parsed_result = RegistryRegisterVersionActivityResult.parse_obj(
        create_response.result)
    lodge_session_id = parsed_result.lodge_session_id
    second_version_activity_id = parsed_result.version_activity_id
    cleanup_items.append((ItemSubType.VERSION,
                         second_version_activity_id))

    # Wait for next step of lifecycle - step 2
    # no meaningful response from this - just check success
    wait_for_full_successful_lifecycle(
        session_id=lodge_session_id,
        get_token=Tokens.user1
    )

    # - check Version properties
    fetched_second_version_activity = cast(ItemVersion, cast(VersionFetchResponse, fetch_item_successfully_parse(
        item_subtype=ItemSubType.VERSION,
        id=second_version_activity_id,
        token=Tokens.user1(),
        model=VersionFetchResponse
    )).item)

    # check the created item is correct
    # from V2
    assert fetched_second_version_activity.from_item_id == revised_item_id
    # to V3
    assert fetched_second_version_activity.to_item_id == second_revised_item_id
    # Should be v3
    assert int(fetched_second_version_activity.new_version_number) == 3
    assert fetched_second_version_activity.owner_username == linked_person_fixture.owner_username

    # - check the prov graph lineage is appropriate

    version_downstream_query = successful_basic_prov_query(
        start=second_version_activity_id,
        direction=Direction.DOWNSTREAM,
        depth=1,
        token=Tokens.user1()
    )
    version_upstream_query = successful_basic_prov_query(
        start=second_version_activity_id,
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
            source=second_revised_item_id,
            target=second_version_activity_id
        ),
        lineage_response=version_downstream_query
    )

    # 2) New item was attributed to Person
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasAttributedTo",
            source=second_revised_item_id,
            target=linked_person_fixture.id
        ),
        lineage_response=person_downstream
    )

    # 3) Registry Version was associated with Person
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasAssociatedWith",
            source=second_version_activity_id,
            target=linked_person_fixture.id
        ),
        lineage_response=version_upstream_query
    )

    # 4) Registry Version used previous version
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="used",
            source=second_version_activity_id,
            target=revised_item_id  # V2
        ),
        lineage_response=version_upstream_query
    )


def test_seed_and_update_async_workflow(linked_person_fixture: ItemPerson) -> None:
    """
    - seed a dataset template
    - update the template to complete
    - wait for async completion
    - check the Create activity was produced and is accurate
    - check the prov graph lineage is appropriate 
    """

    # - seed a dataset template
    seed_resp = cast(DatasetTemplateSeedResponse, parsed_seed_item(token=Tokens.user1(
    ), model=DatasetTemplateSeedResponse, item_subtype=ItemSubType.DATASET_TEMPLATE))
    seed = seed_resp.seeded_item
    assert seed

    cleanup_items.append((ItemSubType.DATASET_TEMPLATE, seed.id))

    # - update the template to complete
    update_resp = parsed_successful_update_item(
        id=seed.id,
        updated_domain_info=get_item_subtype_domain_info_example(
            item_subtype=ItemSubType.DATASET_TEMPLATE
        ),
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=Tokens.user1(),
    )

    # - wait for async completion
    session_id = update_resp.register_create_activity_session_id
    assert session_id, f"Update did not include the session ID"

    # wait for the complete lifecycle - step 1
    create_response = wait_for_full_successful_lifecycle(
        session_id=session_id,
        get_token=Tokens.user1
    )

    assert create_response.result is not None
    parsed_result = RegistryRegisterCreateActivityResult.parse_obj(
        create_response.result)
    lodge_session_id = parsed_result.lodge_session_id
    creation_activity_id = parsed_result.creation_activity_id
    cleanup_items.append((ItemSubType.CREATE, creation_activity_id))

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

    # check the created item is correct
    assert fetched_create_activity.created_item_id == seed.id

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

    # Check for presence of each link

    # 1) Item was generated by registry create
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasGeneratedBy",
            source=seed.id,
            target=creation_activity_id
        ),
        lineage_response=activity_downstream_query
    )

    # 2) Item was attributed to Person
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasAttributedTo",
            source=seed.id,
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
