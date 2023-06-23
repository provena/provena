from SharedInterfaces.RegistryAPI import *
from tests.helpers import get_item_subtype_route_params
import pytest
import pydantic


def test_dataset_template_unique_resource_keys() -> None:
    # Tests that the resource key unique constraint works on the DatasetTemplate

    # create a normal template
    rp = get_item_subtype_route_params(
        item_subtype=ItemSubType.DATASET_TEMPLATE)

    # Check that a proper model validates
    good_template = DatasetTemplateDomainInfo.parse_obj(
        rp.model_examples.domain_info[0].dict())

    # Now modify the model to duplicate a resource key
    deferred = good_template.deferred_resources
    assert (len(deferred) > 0)
    copied = deferred[0]
    deferred.append(copied)

    # Deferred now has duplicates, try and reparse
    with pytest.raises(pydantic.ValidationError):
        bad_template = DatasetTemplateDomainInfo.parse_obj(
            good_template.dict())

    # Now remove it and make sure it's good again
    deferred.pop()
    another_template = DatasetTemplateDomainInfo.parse_obj(
        good_template.dict())


def test_workflow_template_unique_annotation_keys() -> None:
    # Tests that the annotation key unique constraint works on the WorkflowTemplate

    # create a normal template
    rp = get_item_subtype_route_params(
        item_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)

    # Check that a proper model validates
    good_template = ModelRunWorkflowTemplateDomainInfo.parse_obj(
        rp.model_examples.domain_info[0].dict())

    # Now modify the model to duplicate a resource key
    annotations = good_template.annotations
    assert annotations is not None
    required = annotations.required
    optional = annotations.optional
    assert (len(required) > 0)
    assert (len(optional) > 0)

    # Try copying a key from required -> optional
    ex_required = required[0]
    optional.append(ex_required)

    # Now has duplicates, try and reparse
    with pytest.raises(pydantic.ValidationError):
        bad_template = WorkflowTemplateDomainInfo.parse_obj(
            good_template.dict())

    # Now remove that
    optional.pop()

    # Check it passes again
    another_template = WorkflowTemplateDomainInfo.parse_obj(
        good_template.dict())

    # Copy required into itself
    required.append(ex_required)

    # should fail again
    with pytest.raises(pydantic.ValidationError):
        bad_template = WorkflowTemplateDomainInfo.parse_obj(
            good_template.dict())

    # Now remove that
    required.pop()

    # should pass again
    another_template = WorkflowTemplateDomainInfo.parse_obj(
        good_template.dict())

    # And try optional into optional
    ex_optional = optional[0]
    optional.append(ex_optional)

    # should fail again
    with pytest.raises(pydantic.ValidationError):
        bad_template = WorkflowTemplateDomainInfo.parse_obj(
            good_template.dict())
