"""Tests the Generate Report Functionality endpoint stored within PROV-API.

    Relies both on PROV and REGISTRY API for successful testing.
"""

from ProvenaInterfaces.RegistryAPI import *
from KeycloakRestUtilities.Token import BearerAuth

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


"""Need to do the following: 

    1- Create Dataset 
    2- Create Dataset Template 
    3- Create Model Run linked with a study

"""

def test_generate_report_successful(linked_person_fixture: ItemPerson, organisation_fixture: ItemOrganisation, dataset_io_fixture: Tuple[str, str]) -> None: 

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
    response_model_run_record = register_modelrun_from_record_info_successfully(
        get_token=Tokens.user1, 
        model_run_record=model_run_record
    )
    cleanup_items.append((ItemSubType.MODEL_RUN,response_model_run_record.id))

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

def test_generate_report_invalid():

    # Test this endpoint with an invalid item subtype. 

    # Attempt to call this with just a model entity

    model_item = create_item_from_domain_info(

    )





def test_generate_report_model_run():




