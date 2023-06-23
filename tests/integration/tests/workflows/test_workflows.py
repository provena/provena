from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.ProvenanceAPI import *
from tests.helpers.general_helpers import *
from tests.helpers.datastore_helpers import *
from tests.helpers.prov_helpers import *
from tests.helpers.registry_helpers import *
from tests.helpers.link_helpers import *
from resources.example_models import *
from tests.config import config, Tokens
from typing import Generator, cast
import pytest
from uuid import uuid4

cleanup_items: List[Tuple[ItemSubType, IdentifiedResource]] = []

# fixture to clean up items
@pytest.fixture(scope='session', autouse=True)
def entity_cleanup_fixture() -> Generator:
    
    yield
    
    if config.LEAVE_ITEMS_FOR_INITIALISATION:
        print('Skipping entity cleanup for workflow tests - Leaving Items for intialisation of deployment.')
    else:
        print("Performing entity cleanup in workflow tests.")
        perform_entity_cleanup(cleanup_items, token=Tokens.admin())


@pytest.fixture(scope='session', autouse=False)
def person_fixture() -> Generator[ItemPerson, None, None]:
    # create person 1 and 2  (user 1 and 2)
    person = create_item_successfully(
        item_subtype=ItemSubType.PERSON,
        token=Tokens.user1()
    )
    cleanup_items.append((person.item_subtype, person.id))
    # provide to any test that uses them
    yield cast(ItemPerson, person)
    


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
    cleanup_items.append((org.item_subtype, org.id))
    # provide to any test that uses them
    yield cast(ItemOrganisation, org)


@pytest.fixture(scope='session', autouse=False)
def dataset_io_fixture(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> Generator[Tuple[str, str], None, None]:
    # pull out prebuilt references from the fixture
    person = linked_person_fixture
    organisation = organisation_fixture

    # models to test
    cf_1 = valid_collection_format1
    cf_2 = valid_collection_format2

    # create person 1 and 2
    datasets = cast(Tuple[str, str], (
        mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=cf_1,
                display_name=cf_1.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri="")
            )
        ).handle,
        mint_basic_dataset_successfully(
            token=Tokens.user1(),
            author_organisation_id=organisation.id,
            publisher_organisation_id=organisation.id,
            model=DatasetDomainInfo(
                collection_format=cf_2,
                display_name=cf_2.dataset_info.name,
                s3=S3Location(
                    bucket_name="", path="", s3_uri="")
            )
        ).handle))

    cleanup_items.extend([
        (ItemSubType.DATASET, datasets[0]),
        (ItemSubType.DATASET, datasets[1]),
    ])

    # provide to any test that uses them
    yield datasets
    

def test_provenance_workflow(dataset_io_fixture: Tuple[str, str], linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    # prov test that will create the requirements needed for a model run record and register it
    # Procedure:
    # create the simple entities required (person, organisation)
    # register custom dataset templates for input and output datasets
    # register simple model
    # register model run workflow tempalte using references to pre registered entities
    # create and register the model run object using references to pre registered entitites
    person = linked_person_fixture
    organisation = organisation_fixture

    write_token = Tokens.user1

    # register custom dataset templates (input and output)
    input_deferred_resource_key = "key1"
    input_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.DATASET_TEMPLATE,
        token=write_token(),
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
        token=write_token(),
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
        item_subtype=ItemSubType.MODEL, token=write_token())
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
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE, token=write_token(), domain_info=mrwt_domain_info)
    cleanup_items.append((mrwt.item_subtype, mrwt.id))
    description_UUID = "integration test description_UUID: " + str(uuid4())
    # create model run to register
    model_run_record = ModelRunRecord(
        workflow_template_id=mrwt.id,
        inputs=[TemplatedDataset(
            dataset_template_id=input_template.id,
            dataset_id=dataset_io_fixture[0],
            dataset_type=DatasetType.DATA_STORE,
            resources={
                input_deferred_resource_key: '/path/to/resource.csv'
            }
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template.id,
            dataset_id=dataset_io_fixture[1],
            dataset_type=DatasetType.DATA_STORE,
            resources={
                output_deferred_resource_key: '/path/to/resource.csv'
            }
        )],
        associations=AssociationInfo(
            modeller_id=person.id,
            requesting_organisation_id=organisation.id
        ),
        start_time=(datetime.now().timestamp()),
        end_time=(datetime.now().timestamp()),
        description="Integration test fake model run " + description_UUID,
        annotations={
            required_annotation_key: 'somevalue',
            optional_annotation_key: 'some other optional value'
        }
    )

    # register model run
    model_run_id, model_run_record = register_modelrun_from_record_info_successfully_potential_timeout(
        token=write_token(), model_run_record=model_run_record, description_UUID=description_UUID)
    cleanup_items.append((ItemSubType.MODEL_RUN, model_run_id))



def test_create_and_update_history(dataset_io_fixture: Tuple[str, str], linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    write_token = Tokens.user1

    person = linked_person_fixture
    organisation = organisation_fixture


    # Data store API update workflow
    # ==============================
    
    # use one of the provided datasets for testing
    id = dataset_io_fixture[0]

    # fetch
    raw_item = raw_fetch_item_successfully(
        item_subtype=ItemSubType.DATASET, id=id, token=write_token())
    item = DatasetFetchResponse.parse_obj(raw_item).item
    assert item
    assert isinstance(item, ItemBase)

    original_item = item

    # check history
    history = item.history

    # check length
    assert len(
        history) == 1, f"Should have single item in history but had {len(history)}."

    # check item is parsable as type and is equal
    domain_info_model = DatasetDomainInfo
    entry = domain_info_model.parse_obj(history[0].item)
    check_equal_models(entry, domain_info_model.parse_obj(item))

    # check basic properties of the history item
    history_item = history[0]

    # timestamp is reasonable? - NA as this item was created previously
    # check_current_with_buffer(history_item.timestamp)

    # make sure username is correct
    assert history_item.username == config.SYSTEM_WRITE_USERNAME

    # check reason is not empty
    assert history_item.reason != ""

    # grant write
    # --------------
    auth_config = get_auth_config(
        id=id, item_subtype=ItemSubType.DATASET, token=write_token())
    auth_config.general.append("metadata-write")
    put_auth_config(id=id, auth_payload=py_to_dict(auth_config),
                    item_subtype=ItemSubType.DATASET, token=write_token())

    # update (user 2)
    # --------------
    write_token = Tokens.user2

    existing_metadata = entry.collection_format
    existing_metadata.dataset_info.name += "-updated"
    reason = "test reason"
    update_metadata_sucessfully(
        dataset_id=id,
        updated_metadata=py_to_dict(existing_metadata),
        token=write_token(),
        reason=reason
    )

    # check history
    # --------------

    raw_item = raw_fetch_item_successfully(
        item_subtype=ItemSubType.DATASET, id=id, token=write_token())
    item = DatasetFetchResponse.parse_obj(raw_item).item

    assert item
    assert isinstance(item, ItemBase)

    # check history
    history = item.history

    # check length
    assert len(
        history) == 2, f"Should have two items in history but had {len(history)}."

    # check item is parsable as type and is equal
    domain_info_model = DatasetDomainInfo

    first_entry = domain_info_model.parse_obj(history[0].item)
    check_equal_models(first_entry, domain_info_model.parse_obj(item))

    # check basic properties of the history items
    history_item = history[0]

    # timestamp is reasonable?
    check_current_with_buffer(history_item.timestamp)

    # make sure username is correct
    assert history_item.username == config.SYSTEM_WRITE_USERNAME_2

    # check reason is not empty
    assert history_item.reason == reason

    # check basic properties of the history items
    history_item = history[1]

    # make sure username is correct (should be original username)
    assert history_item.username == config.SYSTEM_WRITE_USERNAME

    # check reason is not empty
    assert history_item.reason != ""

    # perform reversion to v1
    # -----------------------

    # identify id and contents from history
    history_id = history[1].id

    # revert to id
    revert_dataset_successfully(
        dataset_id=id,
        reason="integration tests",
        history_id=history_id,
        token=write_token()
    )

    # fetch
    raw_item = raw_fetch_item_successfully(
        item_subtype=ItemSubType.DATASET, id=id, token=write_token())
    item = DatasetFetchResponse.parse_obj(raw_item).item

    assert item
    assert isinstance(item, ItemDataset)

    # check contents after update
    history = item.history

    # check len is > + 1
    assert len(
        history) == 3, f"length of history should be three (two versions + update) but was {len(history)}."

    # also check that the new item has the correct original contents
    check_equal_models(
        DatasetDomainInfo.parse_obj(original_item), DatasetDomainInfo.parse_obj(py_to_dict(history[0].item)))

    # Direct registry API update workflow
    # ===================================

    # use user 1 initially
    write_token = Tokens.user1

    # create Model
    item = ModelCreateResponse.parse_obj(raw_create_item_successfully(
        item_subtype=ItemSubType.MODEL, token=write_token())).created_item
    assert item
    id = item.id

    # make sure model is cleaned up
    cleanup_items.append((ItemSubType.MODEL, id))

    # check history
    history = item.history

    # check length
    assert len(
        history) == 1, f"Should have single item in history but had {len(history)}."

    # check item is parsable as type and is equal
    domain_info_model = ModelDomainInfo
    entry = domain_info_model.parse_obj(history[0].item)
    check_equal_models(entry, domain_info_model.parse_obj(item))

    # check basic properties of the history item
    history_item = history[0]

    # timestamp is reasonable?
    check_current_with_buffer(history_item.timestamp)

    # make sure username is correct
    assert history_item.username == config.SYSTEM_WRITE_USERNAME

    # check reason is not empty
    assert history_item.reason != ""

    # grant write
    # --------------
    auth_config = get_auth_config(
        id=id, item_subtype=ItemSubType.MODEL, token=write_token())
    auth_config.general.append("metadata-write")
    put_auth_config(id=id, auth_payload=py_to_dict(auth_config),
                    item_subtype=ItemSubType.MODEL, token=write_token())

    # update (user 2)
    # --------------
    write_token = Tokens.user2

    existing_metadata = entry
    existing_metadata.display_name += "-updated"
    reason = "test reason"

    resp = update_item(
        id=id,
        updated_domain_info=existing_metadata,
        item_subtype=ItemSubType.MODEL,
        token=write_token(),
        reason=reason
    )
    assert resp.status_code == 200, f"Non 200 code: {resp.status_code}, reason: {resp.text}"

    # check history
    # --------------

    raw_item = raw_fetch_item_successfully(
        item_subtype=ItemSubType.MODEL, id=id, token=write_token())
    item = ModelFetchResponse.parse_obj(raw_item).item

    assert item
    assert isinstance(item, ItemBase)

    # check history
    history = item.history

    # check length
    assert len(
        history) == 2, f"Should have two items in history but had {len(history)}."

    first_entry = domain_info_model.parse_obj(history[0].item)
    check_equal_models(first_entry, domain_info_model.parse_obj(item))

    # check basic properties of the history items
    history_item = history[0]

    # timestamp is reasonable?
    check_current_with_buffer(history_item.timestamp)

    # make sure username is correct
    assert history_item.username == config.SYSTEM_WRITE_USERNAME_2

    # check reason is not empty
    assert history_item.reason == reason

    # check basic properties of the history items
    history_item = history[1]

    # make sure username is correct (should be original username)
    assert history_item.username == config.SYSTEM_WRITE_USERNAME

    # check reason is not empty
    assert history_item.reason != ""

    # perform reversion to v1
    # -----------------------

    # identify id and contents from history
    history_id = history[1].id

    # revert to id
    revert_item_successfully(
        item_subtype=ItemSubType.MODEL,
        id=item.id,
        history_id=history_id,
        token=write_token()
    )

    # fetch
    raw_item = raw_fetch_item_successfully(
        item_subtype=ItemSubType.MODEL, id=id, token=write_token())
    item = ModelFetchResponse.parse_obj(raw_item).item
    assert item
    assert isinstance(item, ItemModel)

    # check contents after update
    history = item.history

    # check len is > + 1
    assert len(
        history) == 3, f"length of history should be three (two versions + update) but was {len(history)}."

    # also check that the new item has the correct original contents
    check_equal_models(
        domain_info_model.parse_obj(item), ModelDomainInfo.parse_obj(py_to_dict(history[0].item)))
