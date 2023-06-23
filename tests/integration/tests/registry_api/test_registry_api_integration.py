import requests
from KeycloakRestUtilities.Token import BearerAuth
from SharedInterfaces.RegistryAPI import *
from tests.helpers.datastore_helpers import mint_basic_dataset_successfully
from tests.helpers.registry_helpers import *
from tests.helpers.auth_helpers import *
import pytest  # type: ignore
from tests.config import Tokens, config
from tests.helpers.link_helpers import *
from resources.example_models import *
from typing import Generator, cast

cleanup_group_ids: List[str] = []
cleanup_items: List[Tuple[ItemSubType, IdentifiedResource]] = []

# fixture to clean up groups


@pytest.fixture(scope='session', autouse=True)
def group_cleanup_fixture() -> Generator:
    # start up code here:
    yield
    # clean up code here:
    perform_group_cleanup(
        cleanup_group_ids=cleanup_group_ids, token=Tokens.admin())

# fixture to clean up items


@pytest.fixture(scope='session', autouse=True)
def entity_cleanup_fixture() -> Generator:
    yield
    perform_entity_cleanup(cleanup_items, token=Tokens.admin())


def test_integration_list_all() -> None:
    token = Tokens.user1
    assert token is not None
    list_endpoint = config.REGISTRY_API_ENDPOINT + "/registry/general/list"
    response = requests.post(list_endpoint,
                             auth=BearerAuth(token()),
                             json={}  # currently expects a payload even if it's empty
                             )
    assert response.status_code == 200, f'Status code is not 200, response message: {response.text}'
    list_registry_response = GenericListResponse.parse_obj(response.json())
    assert list_registry_response.status.success


def test_item_auth_and_edit_workflow() -> None:
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


def test_list() -> None:
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

    token = Tokens.user1()

    # get person domain info
    person_domain_info = get_item_subtype_domain_info_example(
        item_subtype=ItemSubType.PERSON)
    # make a copy so we are not altering the example directly so it can be used in other tests as is
    person_domain_info = PersonDomainInfo.parse_obj(person_domain_info.dict())

    # create person successfully
    person_item = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.PERSON, token=token, domain_info=person_domain_info)
    cleanup_items.append((ItemSubType.PERSON, person_item.id))
    # fetch person and ensure it is ethics approved
    person_item = fetch_complete_person_item_successfully(
        id=person_item.id, token=token)
    assert person_item.ethics_approved, f"Expected fetched item to have ethics approved. Got {person_item.ethics_approved} instead."

    # update person to not be ethics approved
    person_domain_info.ethics_approved = False
    update_resp = update_item(
        id=person_item.id,
        token=token,
        item_subtype=ItemSubType.PERSON,
        updated_domain_info=person_domain_info
    )
    # check status 200 but with error in response
    assert update_resp.status_code == 200, f"Expected 200, recieved {update_resp.status_code}."
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, f"Expected update to fail. Got {update_resp.status.success} instead."

    # fetch person and ensure it is still ethics approved
    person_item = fetch_complete_person_item_successfully(
        id=person_item.id, token=token)
    assert person_item.ethics_approved, f"Expected fetched item to have ethics approved. Got {person_item.ethics_approved} instead."

    # try create person without ethics approved and ensure failure
    person_domain_info.ethics_approved = False
    create_resp = create_item_from_domain_info(
        item_subtype=ItemSubType.PERSON, token=token, domain_info=person_domain_info)
    # check status 200 but with error in response
    assert create_resp.status_code == 200, f"Expected 200, recieved {create_resp.status_code}."
    create_resp = StatusResponse.parse_obj(create_resp.json())
    assert not create_resp.status.success, f"Expected create to fail due to no ethics approval. Got {create_resp.status.success} instead."


def test_invalid_mrwt_update() -> None:
    # Test that will create the requirements needed for a MRWT register it succesfully, then,
    # will try to update the MRWT with invalid handle references and ensure failure

    write_token = Tokens.user1()

    # register custom dataset templates (input and output)
    input_deferred_resource_key = "key1"
    input_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=write_token,
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

    output_deferred_resource_key = "Key2"
    output_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=write_token,
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

    # regiter the model used in the model run
    model = create_item_successfully(
        item_subtype=ItemSubType.MODEL, token=write_token)
    cleanup_items.append((model.item_subtype, model.id))

    # create and register model run workflow template
    required_annotation_key = "annotation_key1"
    optional_annotation_key = "annotation_key2"
    mrwt_domain_info = ModelRunWorkflowTemplateDomainInfo(
        display_name="IntegrationTestMRWT",
        software_id=model.id,  # model is software
        software_version="v1.17",
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
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE, token=write_token, domain_info=mrwt_domain_info)
    cleanup_items.append((mrwt.item_subtype, mrwt.id))

    # update mrwt domain info with invalid handles one by one and test ensure failure to validate by checking 200 but failure in status.

    # make invalid software id and ensure exception
    mrwt_domain_info.software_id = "invalid_software_id"
    update_resp = update_item(id=mrwt.id, token=write_token, updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid software id but got success"

    # make invalid input template id and ensure exception
    mrwt_domain_info.software_id = model.id
    mrwt_domain_info.input_templates[0].template_id = "invalid_input_template_id"
    update_resp = update_item(id=mrwt.id, token=write_token, updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid input template id but got success"

    # make invalid output template id and ensure exception
    mrwt_domain_info.input_templates[0].template_id = input_template.id
    mrwt_domain_info.output_templates[0].template_id = "invalid_output_template_id"
    update_resp = update_item(id=mrwt.id, token=write_token, updated_domain_info=mrwt_domain_info,
                              item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)
    assert update_resp.status_code == 200, "Expected 200 but with success failure"
    update_resp = StatusResponse.parse_obj(update_resp.json())
    assert not update_resp.status.success, "Expected failure due to invalid output template id but got success"
