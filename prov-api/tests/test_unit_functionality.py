import tests.env_setup
from datetime import datetime, date
from typing import Any
from config import Config, base_config
from helpers.entity_validators import RequestStyle
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.RegistryAPI import *
import pytest
from helpers.template_helpers import get_headers_list
from tests.test_config import *


@pytest.mark.asyncio
async def test_validate_model_run_record(monkeypatch: Any) -> None:
    # setup function mocks which are constant

    import helpers.validate_model_run_record

    # validate datastore resource

    async def validate_datastore_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[str, SeededItem, ItemDataset]:
        return ItemDataset(
            id="test",
            display_name="test",
            owner_username="1234",
            item_category=ItemCategory.ENTITY,
            item_subtype=ItemSubType.DATASET,
            record_type=RecordType.COMPLETE_ITEM,
            collection_format=CollectionFormat(
                associations=CollectionFormatAssociations(
                    organisation_id="1234"
                ),
                approvals=CollectionFormatApprovals(
                    ethics_registration=DatasetEthicsRegistrationCheck(),
                    ethics_access=DatasetEthicsAccessCheck(),
                    indigenous_knowledge=IndigenousKnowledgeCheck(
                    ),
                    export_controls=ExportControls(
                    )
                ),
                dataset_info=CollectionFormatDatasetInfo(
                    name="test",
                    description="test",
                    publisher_id="1234",
                    created_date=date.today(),
                    published_date=date.today(),
                    license="http://fake.com",
                    access_info=AccessInfo(reposited=True),
                )
            ),
            s3=S3Location(bucket_name="test", path="test", s3_uri="test"),
            release_status=ReleasedStatus.NOT_RELEASED,
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            history=[]
        )

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_datastore_id',
        validate_datastore_id_mock
    )

    # validate model ID

    async def validate_model_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[ItemModel, SeededItem, str]:
        return ItemModel(
            id=id,
            owner_username="1234",
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            record_type=RecordType.COMPLETE_ITEM,
            display_name="test",
            description="test",
            documentation_url="https://test.com",
            source_url="https://test.com",
            name="fake",
            history=[]
        )

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_model_id',
        validate_model_id_mock
    )

    # validate person ID

    async def validate_person_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[ItemPerson, SeededItem, str]:
        return ItemPerson(
            id=id,
            owner_username="1234",
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            record_type=RecordType.COMPLETE_ITEM,
            display_name="test",
            first_name="test",
            last_name="test",
            email="test@gmail.com",
            history=[],
            ethics_approved=True,
        )

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_person_id',
        validate_person_id_mock
    )

    # validate organisation ID

    async def validate_organisation_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[ItemOrganisation, SeededItem, str]:
        return ItemOrganisation(
            id=id,
            owner_username="1234",
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            record_type=RecordType.COMPLETE_ITEM,
            display_name="test",
            name="test",
            history=[]
        )

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_organisation_id',
        validate_organisation_id_mock
    )

    # validate study ID

    async def validate_study_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[ItemStudy, SeededItem, str]:
        return ItemStudy(
            id=id,
            owner_username="1234",
            created_timestamp=int(datetime.now().timestamp()),
            updated_timestamp=int(datetime.now().timestamp()),
            display_name="test",
            title="Test Study",
            description="Test Study",
            history=[],
            record_type=RecordType.COMPLETE_ITEM
        )

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_study_id',
        validate_study_id_mock
    )

    # helper function to generate model run workflow template mocks

    def produce_mocked_validate_workflow(input_templates: List[TemplateResource], output_templates: List[TemplateResource], annotations: Optional[WorkflowTemplateAnnotations]) -> Any:
        async def mocked_validate_workflow_template(id: str, config: Config, request_style: RequestStyle) -> Union[ItemModelRunWorkflowTemplate, SeededItem, str]:
            return ItemModelRunWorkflowTemplate(
                owner_username="1234",
                display_name="fake",
                software_id="fake",
                software_version="v.1.fake",
                input_templates=input_templates,
                output_templates=output_templates,
                id=id,
                annotations=annotations,
                created_timestamp=int(datetime.now().timestamp()),
                updated_timestamp=int(datetime.now().timestamp()),
                record_type=RecordType.COMPLETE_ITEM,
                history=[]
            )
        return mocked_validate_workflow_template

    # helper function to generate dataset template mocks

    def produce_mocked_dataset_template(defined_map: Dict[str, List[DefinedResource]], deferred_map: Dict[str, List[DeferredResource]]) -> Any:
        async def validate_dataset_template_id(id: str, config: Config, request_style: RequestStyle) -> Union[ItemDatasetTemplate, SeededItem, str]:
            return ItemDatasetTemplate(
                display_name="fake",
                owner_username="1234",
                id=id,
                created_timestamp=int(datetime.now().timestamp()),
                updated_timestamp=int(datetime.now().timestamp()),
                record_type=RecordType.COMPLETE_ITEM,
                defined_resources=defined_map[id],
                deferred_resources=deferred_map[id],
                history=[]
            )

        return validate_dataset_template_id

    # Test a successful validation with no annotations or deferred resources
    input_template_id = "input_id"
    output_template_id = "output_id"
    workflow_template = produce_mocked_validate_workflow(
        input_templates=[TemplateResource(
            template_id=input_template_id
        )],
        output_templates=[
            TemplateResource(
                template_id=output_template_id
            )
        ],
        annotations=None
    )

    # apply patch
    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_model_run_workflow_template',
        workflow_template
    )

    # Setup input/output templates
    def default_defined_resource() -> DefinedResource: return DefinedResource(
        usage_type=ResourceUsageType.GENERAL_DATA,
        description="test",
        path="/"
    )

    defined_map = {
        input_template_id: [default_defined_resource()],
        output_template_id: [default_defined_resource()]
    }
    deferred_map: Dict[str, List[DeferredResource]] = {
        input_template_id: [],
        output_template_id: []
    }

    # setup the dataset template mock(s)
    dataset_template = produce_mocked_dataset_template(
        defined_map=defined_map,
        deferred_map=deferred_map
    )

    # apply patch
    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_dataset_template_id',
        dataset_template
    )

    # produce the model run record payload
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE)],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE)],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        start_time=int(datetime.now().timestamp()),
        display_name="test display name",
        description="test description",
        end_time=int(datetime.now().timestamp())
    )

    # Fake config
    fake_config = Config(
        stage=stage,
        keycloak_endpoint=base_config.keycloak_endpoint,
        service_account_secret_arn="",
        # This should not be used
        job_api_endpoint="",
        registry_api_endpoint="",
        mock_graph_db=True,
        neo4j_host="",
        neo4j_port=0,
        neo4j_test_username="",
        neo4j_test_password="",
        depth_default_limit=30,
        depth_upper_limit=100,
    )

    fake_request_style = RequestStyle(
        user_direct=None,
        service_account=None
    )

    # lodge it and make sure it validates
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert success, f"Validation failed with mocked functions, error reported: {error}"

    # produce a model run record payload with invalid times
    model_run_record_invalid_times = ModelRunRecord.parse_obj(
        model_run_record.dict())
    model_run_record_invalid_times.start_time = 1
    model_run_record_invalid_times.end_time = 0

    # lodge it and make sure it doesn't validate
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record_invalid_times,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should've failed with an end time before the start time."

    # try setting up a study ID - should succeed
    model_run_record_invalid_study_id = ModelRunRecord.parse_obj(
        model_run_record.dict())

    model_run_record_invalid_study_id.study_id = "1234"

    # lodge it and make sure it validates
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record_invalid_study_id,
        config=fake_config,
        request_style=fake_request_style
    )

    assert success, f"Providing study id with mocked validation response should have succeeded"

    # validate study ID

    async def non_valid_study_id_mock(id: str, config: Config, request_style: RequestStyle) -> Union[ItemStudy, SeededItem, str]:
        return "Test setup to fail id for study id"

    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_study_id',
        non_valid_study_id_mock
    )

    # lodge it and make sure it doesn't validate
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record_invalid_study_id,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Providing study id with mocked invalid response should have failed"

    # return mock
    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_study_id',
        validate_study_id_mock
    )

    # Now let's try adding a resource with a key + an annotation

    # Test a successful validation with no annotations or deferred resources
    annotation_key = "annotation"
    workflow_template = produce_mocked_validate_workflow(
        input_templates=[TemplateResource(
            template_id=input_template_id
        )],
        output_templates=[
            TemplateResource(
                template_id=output_template_id
            )
        ],
        annotations=WorkflowTemplateAnnotations(
            required=[annotation_key],
            optional=[]
        )
    )

    # apply patch
    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_model_run_workflow_template',
        workflow_template
    )

    defined_map = {
        input_template_id: [default_defined_resource()],
        output_template_id: [default_defined_resource()]
    }

    def generate_deferred(resource_key: str) -> DeferredResource:
        return DeferredResource(
            usage_type=ResourceUsageType.GENERAL_DATA,
            description="fake",
            key=resource_key
        )

    input_resource_key = "input_resource"
    output_resource_key = "output_resource"
    deferred_map = {
        input_template_id: [generate_deferred(input_resource_key)],
        output_template_id: [generate_deferred(output_resource_key)]
    }

    # setup the dataset template mock(s)
    dataset_template = produce_mocked_dataset_template(
        defined_map=defined_map,
        deferred_map=deferred_map
    )

    # apply patch
    monkeypatch.setattr(
        helpers.validate_model_run_record,
        'validate_dataset_template_id',
        dataset_template
    )

    # produce the model run record payload
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert success, f"Validation failed with mocked functions, error reported: {error}"

    # now remove an input resource and make sure it fails
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should have failed due to removing a required resource but it did not"

    # now remove an output resource and make sure it fails
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should have failed due to removing a required resource but it did not"

    # now remove both resources and make sure it fails
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should have failed due to removing a required resource but it did not"

    # now add an output key into input and make sure it fails
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake", output_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should have failed due to removing a required resource but it did not"

    # now add an unknown key
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake", 'extra_key': "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation should have failed due to removing a required resource but it did not"

    # now make sure successful lodge still works
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake annotation"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert success, f"Validation failed with mocked functions, error reported: {error}"

    # now remove an annotation
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert not success, f"Validation succeeded but should have failed due to missing annotation"

    # now add an annotation - this should be okay
    model_run_record = ModelRunRecord(
        workflow_template_id="workflowtemplate",
        inputs=[TemplatedDataset(
            dataset_template_id=input_template_id,
            dataset_id="inputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={input_resource_key: "fake"}
        )],
        outputs=[TemplatedDataset(
            dataset_template_id=output_template_id,
            dataset_id="outputdataset",
            dataset_type=DatasetType.DATA_STORE,
            resources={output_resource_key: "fake"}
        )],
        associations=AssociationInfo(
            modeller_id="modeller", requesting_organisation_id="organisation"),
        display_name="test display name",
        description="test description",
        start_time=int(datetime.now().timestamp()),
        end_time=int(datetime.now().timestamp()),
        annotations={
            annotation_key: "Fake",
            'extra_annotation': "Should be fine"
        }
    )
    success, error = await helpers.validate_model_run_record.validate_model_run_record(
        record=model_run_record,
        config=fake_config,
        request_style=fake_request_style
    )

    assert success, f"Validation should have succeeded with an extra annotation key, but failed with {error}."


def test_csv_headers_parsing() -> None:

    header_str = """"my,header1,with,commas",header2,header3,"header,4,w,commas","""
    headers = get_headers_list(header_str)

    assert headers[0] == "my,header1,with,commas"
    assert headers[1] == "header2"
    assert headers[2] == "header3"
    assert headers[3] == 'header,4,w,commas'
