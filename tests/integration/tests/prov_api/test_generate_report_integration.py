"""Tests the Generate Report Functionality endpoint stored within PROV-API.

    Relies both on PROV and REGISTRY API for successful testing.
"""

from ProvenaInterfaces.RegistryAPI import *
from tests.config import Tokens
from tests.helpers.fixtures import *
from tests.helpers.prov_api_helpers import *
from tests.helpers.general_helpers import parse_assert_json_response

@pytest.fixture(scope="function")
def study_linked_to_model_run(
    linked_person_fixture: ItemPerson, 
    organisation_fixture: ItemOrganisation, 
    dataset_io_fixture: Tuple[str, str]
) -> Tuple[ItemBase, ProvenanceRecordInfo]:
    """Creates a study linked to a single model run for testing.

    Parameters
    ----------
    linked_person_fixture : ItemPerson
        Fixture that provides a linked person for testing.
    organisation_fixture : ItemOrganisation
        Fixture that provides an organisation for testing.
    dataset_io_fixture : Tuple[str, str]
        Fixture that provides input and output dataset handles.

    Returns
    -------
    Tuple[ItemBase, ProvenanceRecordInfo]
        The created study item and model run record.
    """
    
    person = linked_person_fixture
    organisation = organisation_fixture
    dataset_1_handle, dataset_2_handle = dataset_io_fixture

    # Create templates
    input_template = create_item_successfully(ItemSubType.DATASET_TEMPLATE, token=Tokens.user1())
    output_template = create_item_successfully(ItemSubType.DATASET_TEMPLATE, token=Tokens.user1())
    cleanup_items.append((ItemSubType.DATASET_TEMPLATE,input_template.id))
    cleanup_items.append((ItemSubType.DATASET_TEMPLATE,output_template.id))

    # Create model
    model_item = create_item_successfully(ItemSubType.MODEL, token=Tokens.user1())
    cleanup_items.append((ItemSubType.MODEL,model_item.id))

    # Create model run workflow template
    required_annotation_key = "annotation_key1"
    optional_annotation_key = "annotation_key2"
    model_run_workflow_template_domain_info = ModelRunWorkflowTemplateDomainInfo(
        display_name="IntegrationTestMRWT",
        software_id=model_item.id,  # model is software
        input_templates=[TemplateResource(
            template_id=input_template.id, optional=False)],
        output_templates=[TemplateResource(
            template_id=output_template.id, optional=False)],
        annotations=WorkflowTemplateAnnotations(
            required=[required_annotation_key],
            optional=[optional_annotation_key]
        ),
        user_metadata=None
    )

    model_run_workflow_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
        token=Tokens.user1(),
        domain_info=model_run_workflow_template_domain_info
    )
    cleanup_items.append((ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,model_run_workflow_template.id))

    # Create study entity 
    study_item = create_item_successfully(item_subtype=ItemSubType.STUDY, token=Tokens.user1())
    cleanup_items.append((ItemSubType.STUDY,study_item.id))

    # Create Model Run Domain Info object and link it to the study. 
    model_run_record = ModelRunRecord(
        workflow_template_id=model_run_workflow_template.id,
        inputs=[TemplatedDataset(
            dataset_template_id=input_template.id,
            dataset_id=dataset_1_handle,
            dataset_type=DatasetType.DATA_STORE,
            resources={"item_key": "some-key"}

        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template.id,
            dataset_id=dataset_2_handle,
            dataset_type=DatasetType.DATA_STORE,
            resources={"item_key": "some-key"}
        )],
        associations=AssociationInfo(
            modeller_id=person.id,
            requesting_organisation_id=organisation.id
        ),
        display_name="Integration test fake model run display name",
        start_time=int((datetime.now().timestamp())),
        end_time=int((datetime.now().timestamp())),
        description="Integration test fake model run",
        # Link to a study
        study_id=study_item.id,
        annotations={
            required_annotation_key: 'somevalue',
            optional_annotation_key: 'some other optional value'
        }
    )

    # Register the model run
    created_model_run_record = register_modelrun_from_record_info_successfully(
        get_token=Tokens.user1, 
        model_run_record=model_run_record
    )
    cleanup_items.append((ItemSubType.MODEL_RUN,created_model_run_record.id))

    return study_item, created_model_run_record


@pytest.fixture(scope="function")
def study_linked_to_multiple_model_run(
    linked_person_fixture: ItemPerson, 
    organisation_fixture: ItemOrganisation, 
    dataset_io_fixture: Tuple[str, str]
) -> Tuple[ItemBase, List[ProvenanceRecordInfo]]:
    """Creates a study linked to multiple model runs for testing.

    Parameters
    ----------
    linked_person_fixture : ItemPerson
        Fixture that provides a linked person for testing.
    organisation_fixture : ItemOrganisation
        Fixture that provides an organisation for testing.
    dataset_io_fixture : Tuple[str, str]
        Fixture that provides input and output dataset handles.

    Returns
    -------
    Tuple[ItemBase, List[ProvenanceRecordInfo]]
        The created study item and list of model run records.
    """
    
    person = linked_person_fixture
    organisation = organisation_fixture
    dataset_1_handle, dataset_2_handle = dataset_io_fixture

    # Create templates
    input_template = create_item_successfully(ItemSubType.DATASET_TEMPLATE, token=Tokens.user1())
    output_template = create_item_successfully(ItemSubType.DATASET_TEMPLATE, token=Tokens.user1())
    cleanup_items.append((ItemSubType.DATASET_TEMPLATE,input_template.id))
    cleanup_items.append((ItemSubType.DATASET_TEMPLATE,output_template.id))

    # Create model
    model_item = create_item_successfully(ItemSubType.MODEL, token=Tokens.user1())
    cleanup_items.append((ItemSubType.MODEL,model_item.id))

    # Create model run workflow template
    required_annotation_key = "annotation_key1"
    optional_annotation_key = "annotation_key2"
    model_run_workflow_template_domain_info = ModelRunWorkflowTemplateDomainInfo(
        display_name="IntegrationTestMRWT",
        software_id=model_item.id,  # model is software
        input_templates=[TemplateResource(
            template_id=input_template.id, optional=False)],
        output_templates=[TemplateResource(
            template_id=output_template.id, optional=False)],
        annotations=WorkflowTemplateAnnotations(
            required=[required_annotation_key],
            optional=[optional_annotation_key]
        ),
        user_metadata=None
    )

    model_run_workflow_template = create_item_from_domain_info_successfully(
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
        token=Tokens.user1(),
        domain_info=model_run_workflow_template_domain_info
    )
    cleanup_items.append((ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,model_run_workflow_template.id))

    # Create study entity 
    study_item = create_item_successfully(item_subtype=ItemSubType.STUDY, token=Tokens.user1())
    cleanup_items.append((ItemSubType.STUDY,study_item.id))

    # Create Model Run Domain Info object and link it to the study. 
    list_of_created_model_runs: List[ProvenanceRecordInfo] = []

    for i in range(2):
        model_run_record = ModelRunRecord(
            workflow_template_id=model_run_workflow_template.id,
            inputs=[TemplatedDataset(
                dataset_template_id=input_template.id,
                dataset_id=dataset_1_handle,
                dataset_type=DatasetType.DATA_STORE,
                resources={"item_key": f"some-key - {i}"}

            )],
            outputs=[TemplatedDataset(
                dataset_template_id=output_template.id,
                dataset_id=dataset_2_handle,
                dataset_type=DatasetType.DATA_STORE,
                resources={"item_key": f"some-key - {i}"}
            )],
            associations=AssociationInfo(
                modeller_id=person.id,
                requesting_organisation_id=organisation.id
            ),
            display_name=f"Integration test fake model run display name - {i}",
            start_time=int((datetime.now().timestamp())),
            end_time=int((datetime.now().timestamp())),
            description=f"Integration test fake model run - {i}",
            # Link to a study
            study_id=study_item.id,
            annotations={
                required_annotation_key: f'somevalue - {i}',
                optional_annotation_key: f'some other optional value - {i}'
            }
        )

        # Register the model run
        created_model_run_record = register_modelrun_from_record_info_successfully(
            get_token=Tokens.user1, 
            model_run_record=model_run_record
        )
        cleanup_items.append((ItemSubType.MODEL_RUN,created_model_run_record.id))
        list_of_created_model_runs.append(created_model_run_record)

    return study_item, list_of_created_model_runs

def test_generate_report_from_study_and_model_run(study_linked_to_model_run: Tuple[ItemBase, ProvenanceRecordInfo]) -> None: 
    """Tests generating a report from a study and model run entity.

    Parameters
    ----------
    study_linked_to_model_run : Tuple[ItemBase, ProvenanceRecordInfo]
        Tuple containing a study item and its linked model run record.
    """

    study_item, model_run_record = study_linked_to_model_run

    # Test 1: Generate a report successfully from study entity.
    # Now based on the created study-id call the generate-report-endpoint
    response_content = generate_report_successfully(
        token=Tokens.user1(), 
        node_id=study_item.id,
        upstream_depth=2, 
        item_subtype=study_item.item_subtype)

    # Assert that the response content is not None and contains bytes
    assert response_content is not None, "Expected non-empty response content, got None"
    assert isinstance(response_content, (bytes, bytearray)), f"Expected response to be bytes or bytearray, got {type(response_content)}"
    assert len(response_content) > 0, "Expected non-empty byte content, but response is empty"

    # Test 2: Generate a report succesfully from a model run entity. 
    response_content = generate_report_successfully(
        token=Tokens.user1(), 
        node_id=model_run_record.id,
        upstream_depth=2, 
        item_subtype=ItemSubType.MODEL_RUN)

    # Assert that the response content is not None and contains bytes
    assert response_content is not None, "Expected non-empty response content, got None"
    assert isinstance(response_content, (bytes, bytearray)), f"Expected response to be bytes or bytearray, got {type(response_content)}"
    assert len(response_content) > 0, "Expected non-empty byte content, but response is empty"

    # Test 3: Generate report with invalid upstream depth
    response: Response = generate_report(
        token=Tokens.user1(),
        node_id=study_item.id, 
        upstream_depth=-1,
        item_subtype=study_item.item_subtype
    )

    parse_assert_json_response(
        response=response,
        expected_status_code=422
    )

def test_generate_report_with_multiple_model_runs(study_linked_to_multiple_model_run: Tuple[ItemBase, List[ProvenanceRecordInfo]]) -> None:
    """Tests generating a report from a study linked to multiple model runs.

    Parameters
    ----------
    study_linked_to_multiple_model_run : Tuple[ItemBase, List[ProvenanceRecordInfo]]
        Tuple containing a study item and a list of linked model run records.
    """

    study_item, model_run_record_list = study_linked_to_multiple_model_run
    response_content = generate_report_successfully(
        token=Tokens.user1(), 
        node_id=study_item.id,
        upstream_depth=2, 
        item_subtype=study_item.item_subtype)

    # Assert that the response content is not None and contains bytes
    assert response_content is not None, "Expected non-empty response content, got None"
    assert isinstance(response_content, (bytes, bytearray)), f"Expected response to be bytes or bytearray, got {type(response_content)}"
    assert len(response_content) > 0, "Expected non-empty byte content, but response is empty"

def test_generate_report_with_invalid_subtype(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    """Tests generating a report with an invalid item subtype.

    Parameters
    ----------
    linked_person_fixture : ItemPerson
        Fixture providing a linked person for testing.
    organisation_fixture : ItemOrganisation
        Fixture providing an organisation for testing.
    """

    expected_base_error_message = "Unsupported item subtype for validation."

    # Create a model entity.
    model_item = create_item_successfully(
        item_subtype=ItemSubType.MODEL,
        token=Tokens.user1()
    )
    cleanup_items.append((ItemSubType.MODEL,model_item.id))

    # Call endpoint with invalid subtype entity
    response: Response = generate_report(
        token=Tokens.user1(),
        node_id=model_item.id,
        upstream_depth=1, 
        item_subtype=model_item.item_subtype
    )

    parse_assert_json_response(
        response=response, 
        expected_status_code=400,
        expected_error_message=expected_base_error_message,
        expected_field_key="detail"
    )

def test_generate_report_with_invalid_study_entity() -> None:
    """Tests generating a report with an invalid study entity."""

    fake_id: str = "fake10.3456/7"

    response = generate_report(
        token=Tokens.user1(),
        node_id=fake_id,
        upstream_depth=1,
        item_subtype=ItemSubType.STUDY
    )

    parse_assert_json_response(
        response=response,
        expected_status_code=400,
        expected_error_message="Validation error with provided STUDY: Failed to retrieve item",
        expected_field_key="detail"
    )

def test_valid_study_entity_with_no_connections(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation) -> None:
    """Tests generating a report from a valid study entity with no connections.

    Parameters
    ----------
    linked_person_fixture : ItemPerson
        Fixture providing a linked person for testing.
    organisation_fixture : ItemOrganisation
        Fixture providing an organisation for testing.
    """

    # Create a study entity 
    study_item = create_item_successfully(
        item_subtype=ItemSubType.STUDY,
        token=Tokens.user1()
    )
    cleanup_items.append((ItemSubType.STUDY,study_item.id))

    # Expected base error message 
    expected_base_error_message = f"The study with id {study_item.id} does not have any associated model runs."

    # Call the endpoint and see the response type. 
    response: Response = generate_report(
        token=Tokens.user1(),
        node_id=study_item.id,
        upstream_depth=1,
        item_subtype=study_item.item_subtype
    )

    parse_assert_json_response(
        response=response, 
        expected_status_code=404,
        expected_error_message=expected_base_error_message,
        expected_field_key="detail"
    )
