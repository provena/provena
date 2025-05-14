from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.ProvenanceAPI import *
from tests.helpers.general_helpers import *
from tests.helpers.datastore_helpers import *
from tests.helpers.prov_helpers import *
from tests.helpers.registry_helpers import *
from tests.helpers.link_helpers import *
from resources.example_models import *
from tests.config import config, Tokens
from tests.helpers.fixtures import *
from tests.helpers.prov_api_helpers import *


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

    # cleanup create activity
    cleanup_create_activity_from_item_base(
        item=input_template,
        get_token=Tokens.user1
    )

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

    # cleanup create activity
    cleanup_create_activity_from_item_base(
        item=output_template,
        get_token=Tokens.user1
    )

    # regiter the model used in the model run
    model = create_item_successfully(
        item_subtype=ItemSubType.MODEL, token=write_token())
    cleanup_items.append((model.item_subtype, model.id))

    # cleanup create activity
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
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE, token=write_token(), domain_info=mrwt_domain_info)
    cleanup_items.append((mrwt.item_subtype, mrwt.id))

    # cleanup create activity
    cleanup_create_activity_from_item_base(
        item=mrwt,
        get_token=Tokens.user1
    )

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
        display_name="Integration test fake model run display name",
        start_time=(datetime.now().timestamp()),
        end_time=(datetime.now().timestamp()),
        description="Integration test fake model run",
        annotations={
            required_annotation_key: 'somevalue',
            optional_annotation_key: 'some other optional value'
        }
    )

    # register model run
    response_model_run_record = register_modelrun_from_record_info_successfully(
        get_token=write_token, model_run_record=model_run_record)
    model_run_id = response_model_run_record.id
    cleanup_items.append((ItemSubType.MODEL_RUN, model_run_id))

    # create model run to register including a linked study
    study = create_item_successfully(
        item_subtype=ItemSubType.STUDY, token=write_token())
    cleanup_items.append((study.item_subtype, study.id))

    model_run_record.study_id = study.id

    # register model run
    response_model_run_record = register_modelrun_from_record_info_successfully(
        get_token=write_token, model_run_record=model_run_record)
    model_run_id = response_model_run_record.id
    cleanup_items.append((ItemSubType.MODEL_RUN, model_run_id))


    # - check the prov graph lineage is appropriate

    # The lineage should have

    activity_upstream_query = successful_basic_prov_query(
        start=model_run_id,
        direction=Direction.UPSTREAM,
        depth=1,
        token=Tokens.user1()
    )

    # model run -wasInformedBy-> study
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasInformedBy",
            source=model_run_id,
            target=study.id
        ),
        lineage_response=activity_upstream_query
    )


    # ensure invalid study id results in failure
    model_run_record.study_id = '1234'

    # register model run
    failed, possible_model_run_record = register_modelrun_from_record_info_failed(
        get_token=write_token, model_run_record=model_run_record, expected_code=400)

    if not failed:
        assert possible_model_run_record
        model_run_id = possible_model_run_record.id
        cleanup_items.append((ItemSubType.MODEL_RUN, model_run_id))
        assert False, f"Model run registration with invalid study should have failed, but did not."

    # register a model run without a study, check no upstreamstudy, then add a study using the edit/link_to_study route,check upstream has study.
    model_run_record.study_id = None
    response_model_run_record = register_modelrun_from_record_info_successfully(
        get_token=write_token, model_run_record=model_run_record)
    model_run_id = response_model_run_record.id
    cleanup_items.append((ItemSubType.MODEL_RUN, model_run_id))

    # fetch model run
    model_run_fetch = fetch_item_successfully_parse(item_subtype=ItemSubType.MODEL_RUN, id=model_run_id, token=write_token(), model=ModelRunFetchResponse)
    assert isinstance(model_run_fetch, ModelRunFetchResponse)
    model_run = model_run_fetch.item
    assert isinstance(model_run, ItemModelRun), f"Model run fetch response was not a model run. Type: {type(model_run)}"
    assert model_run.record.study_id is None, f"Study id should be None but was {model_run.record.study_id}"

    # check err is raised if no study id in prov graph aswell
    activity_upstream_query = successful_basic_prov_query(
        start=model_run_id,
        direction=Direction.UPSTREAM,
        depth=1,
        token=Tokens.user1()
    )

    # model run -wasInformedBy-> study
    with pytest.raises(AssertionError):
        assert_non_empty_graph_property(
            prop=GraphProperty(
                type="wasInformedBy",
                source=model_run_id,
                target=study.id
            ),
            lineage_response=activity_upstream_query
        )

    # link to study
    link_resp = link_model_run_to_study_successfully(token=write_token, study_id=study.id, model_run_id=model_run_id)
    # fetch again and make sure study is linked
    model_run_fetch = fetch_item_successfully_parse(item_subtype=ItemSubType.MODEL_RUN, id=model_run_id, token=write_token(), model=ModelRunFetchResponse)
    assert isinstance(model_run_fetch, ModelRunFetchResponse)
    model_run = model_run_fetch.item
    assert isinstance(model_run, ItemModelRun)
    assert model_run.record.study_id == study.id, f"Study id should be {study.id} but was {model_run.record.study_id}"

    # update model run
    updated_display_name = "Updated model run display name"
    updated_description = "Updated model run description"

    model_run.record.display_name = updated_display_name
    model_run.record.description = updated_description

    update_resp = update_modelrun_from_record_info_successfully(
        get_token=write_token,
        model_run_id=model_run_id,
        model_run_record=model_run.record,
        reason="Integration test model run update",
    )

    # fetch again and ensure the updates were successful
    model_run_fetch = fetch_item_successfully_parse(
        item_subtype=ItemSubType.MODEL_RUN,
        id=model_run_id,
        token=write_token(),
        model=ModelRunFetchResponse,
    )
    assert isinstance(model_run_fetch, ModelRunFetchResponse)
    model_run = model_run_fetch.item
    assert isinstance(model_run, ItemModelRun)
    assert model_run.record.display_name == updated_display_name, f"Model run display name should be {updated_display_name} but was {model_run.record.display_name}"
    assert model_run.record.description == updated_description, f"Model run description should be {updated_description} but was {model_run.record.description}"

    activity_upstream_query = successful_basic_prov_query(
        start=model_run_id,
        direction=Direction.UPSTREAM,
        depth=1,
        token=Tokens.user1()
    )

    # model run -wasInformedBy-> study
    assert_non_empty_graph_property(
        prop=GraphProperty(
            type="wasInformedBy",
            source=model_run_id,
            target=study.id
        ),
        lineage_response=activity_upstream_query
    )


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
        item_subtype=ItemSubType.DATASET, id=id, token=write_token()
    )
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

    # Clean up Create Activity
    cleanup_create_activity_from_item_base(item=item, get_token=write_token)

    # grant write
    # --------------
    auth_config = get_auth_config(
        id=id, item_subtype=ItemSubType.MODEL, token=write_token())
    auth_config.general.append("metadata-write")
    put_auth_config(id=id, auth_payload=py_to_dict(auth_config), 
                    item_subtype=ItemSubType.MODEL, token=write_token(),
    )

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
