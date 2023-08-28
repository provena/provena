from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.ProvenanceModels import *
from helpers.entity_validators import *
from typing import Optional, Tuple, Callable, Coroutine


def validate_annotations(workflow_template: ItemModelRunWorkflowTemplate, model_run_record: ModelRunRecord) -> Tuple[bool, Optional[str]]:
    annotations = workflow_template.annotations
    if annotations is not None:
        required_set = set(annotations.required)
        provided_set = set(
            model_run_record.annotations if model_run_record.annotations is not None else [])
        missing_annotations = required_set - provided_set
        if len(missing_annotations) > 0:
            missing_str = ",".join(missing_annotations)
            return False, f"Missing required annotations with keys: ({missing_str})."

    return True, None


async def validate_datastore_resource(templated_dataset: TemplatedDataset, template: ItemDatasetTemplate, request_style: RequestStyle, config: Config) -> Tuple[bool, Optional[str]]:
    # Check that the ID exists in the datastore
    dataset_id = templated_dataset.dataset_id
    dataset_response = await validate_datastore_id(id=dataset_id, config=config, request_style=request_style)
    if isinstance(dataset_response, str):
        return False, f"Input dataset with id {dataset_id} was not a valid id, error: {dataset_response}"

    # Check that all resources are present if required
    required_only = list(filter(
        # only include items that are not explicitly marked as optional
        lambda resource: not (
            resource.optional is not None and resource.optional),
        template.deferred_resources)
    )

    # pull out expected keys vs provided keys
    mandatory_keys = set(
        [resource.key for resource in required_only])
    valid_keys = set(
        [resource.key for resource in template.deferred_resources])

    provided_keys = set(templated_dataset.resources.keys()
                        if templated_dataset.resources else [])

    missing = mandatory_keys - provided_keys
    extra = provided_keys - valid_keys

    if len(missing) > 0:
        return False, f"The provided templated dataset with id {templated_dataset.dataset_template_id} " + \
            f"and dataset id {templated_dataset.dataset_id} was missing deferred resource paths " + \
            f"for the following required resource keys ({','.join(list(missing))})."

    if len(extra) > 0:
        return False, f"The provided templated dataset with id {templated_dataset.dataset_template_id} " + \
            f"and dataset id {templated_dataset.dataset_id} provided unexpected deferred resource paths " + \
            f"for the following unexpected resource keys ({','.join(list(extra))})."

    return True, None


# DATASET_CLASS_VALIDATION_HOOKS: Dict[DatasetType, Callable[[Any, ItemDatasetTemplate, Config], Coroutine[Any, Any, Tuple[bool, Optional[str]]]]] = {
#    DatasetType.DATA_STORE: validate_datastore_resource,
# }


async def validate_model_run_record(record: ModelRunRecord, request_style: RequestStyle, config: Config) -> Tuple[bool, Optional[str]]:
    """    validate_model_run_record
        Passes through all ID'd components of the model run record and validates
        the IDs in the registry API or data store API. 

        Also applies any additional constraints such as deferred resource paths,
        required KVPs etc.

        Arguments
        ----------
        record : ModelRunRecord
            Provenance model run record

        Returns
        -------
         : Tuple[bool, Optional[str]]
            True/false for valid, optionally an error message if something fails

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # validate start and end times
    if record.end_time < record.start_time:
        return False, f"The end time cannot be before the start time of a model run"

    # ensure display name and description are not empty strings
    if record.display_name == "":
        return False, f"Display name cannot be empty string"
    if record.description == "":
        return False, f"Description cannot be empty string"

    # validate workflow definition
    # ----------------------------

    # fetch the definition from the registry
    workflow_response = await validate_model_run_workflow_template(
        id=record.workflow_template_id,
        request_style=request_style,
        config=config
    )

    # ensure exists and complete
    if isinstance(workflow_response, str):
        return False, f"Provided model run workflow definition with id {record.workflow_template_id} was not a valid id, error: {workflow_response}"
    if isinstance(workflow_response, SeededItem):
        return False, f"Provided model run workflow definition with id {record.workflow_template_id} is an incomplete seed record."

    # validate all workflow definition templates
    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    # collect input/output templates
    input_template_resources: List[TemplateResource] = workflow_response.input_templates
    output_template_resources: List[TemplateResource] = workflow_response.output_templates

    resolved_templates: Dict[str, ItemDatasetTemplate] = {}

    # ensure all templates (in the definition) exist and are complete
    for template_resource in input_template_resources + output_template_resources:
        template_id = template_resource.template_id
        template_response = await validate_dataset_template_id(
            id=template_id,
            config=config,
            request_style=request_style
        )

        # ensure exists and complete
        if isinstance(template_response, str):
            return False, f"Provided dataset template with id {template_id} (associated with the workflow def.) was not a valid id, error: {template_response}"
        if isinstance(template_response, SeededItem):
            return False, f"Provided dataset template with id {template_id} (associated with the workflow def.) is an incomplete seed record."
        # store the resolved template
        assert isinstance(template_response, ItemDatasetTemplate)
        resolved_templates[template_id] = template_response

    # Get provided inputs/outputs and validate existence
    provided_input_templates_list: List[TemplatedDataset] = record.inputs
    provided_output_templates_list: List[TemplatedDataset] = record.outputs

    # produce a dictionary mapping template -> TemplatedDataset

    # inputs
    provided_input_map: Dict[str, List[TemplatedDataset]] = {}
    for input_template in provided_input_templates_list:
        # fetch the matched records and add the entry
        matched_list = provided_input_map.get(
            input_template.dataset_template_id, [])
        matched_list.append(input_template)
        provided_input_map[input_template.dataset_template_id] = matched_list

    # outputs
    provided_output_map: Dict[str, List[TemplatedDataset]] = {}
    for output_template in provided_output_templates_list:
        # fetch the matched records and add the entry
        matched_list = provided_output_map.get(
            output_template.dataset_template_id, [])
        matched_list.append(output_template)
        provided_output_map[output_template.dataset_template_id] = matched_list

    for input_resource in input_template_resources:
        input_id = input_resource.template_id
        if (input_resource.optional is not None) and (input_resource.optional):
            # If optional is provided and set to true then we skip this entry
            # and assume it is found
            continue
        if input_id not in provided_input_map.keys():
            # The required input was not present
            return False, f"The workflow definition expects dataset with template ID {input_id} but it was not present in the inputs."

    for output_resource in output_template_resources:
        output_id = output_resource.template_id
        if (output_resource.optional is not None) and (output_resource.optional):
            # If optional is provided and set to true then we skip this entry
            # and assume it is found
            continue
        if output_id not in provided_output_map.keys():
            # The required output was not present
            return False, f"The workflow definition expects dataset with template ID {output_id} but it was not present in the outputs."

    # validate input contents against templates
    # -----------------------------------------

    # for each input dataset in the prov payload
    for dataset in record.inputs:
        # get type of dataset
        dataset_type = dataset.dataset_type

        try:
            template = resolved_templates[dataset.dataset_template_id]
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"An input template in the payload (id: {dataset.dataset_template_id}) does not exist in the workflow definition's list" +
                " of expected/required input dataset templates." +
                " Check your workflow definition and provided input dataset templates are correct."
            )

        # run validation - checks that the data set exists, that expected
        # deferred resources are present, and that no additional resources are
        # provided
        success, reason = await validate_datastore_resource(
            templated_dataset=dataset,
            template=template,
            request_style=request_style,
            config=config
        )

        # check no error
        if not success:
            return False, f"An input dataset validation process failed, type {dataset_type}, template id {dataset.dataset_template_id}, reason {reason}."

    # validate output contents against templates
    # ------------------------------------------
    # for each output dataset in the prov payload
    for dataset in record.outputs:
        # get type of dataset
        dataset_type = dataset.dataset_type

        try:
            template = resolved_templates[dataset.dataset_template_id]
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"An output template in the payload (id: {dataset.dataset_template_id}) does not exist in the workflow definition's list" +
                " of expected/required output dataset templates." +
                " Check your workflow definition and provided output dataset templates are correct."
            )

        # run validation - checks that the data set exists, that expected
        # deferred resources are present, and that no additional resources are
        # provided
        success, reason = await validate_datastore_resource(
            templated_dataset=dataset,
            template=template,
            request_style=request_style,
            config=config
        )

        # check no error
        if not success:
            return False, f"An output dataset validation process failed, type {dataset_type}, template id {dataset.dataset_template_id}, reason {reason}."

    # validate associations
    # ---------------------
    associations = record.associations

    # model (implicitly through workflow definition)
    model_software_id = workflow_response.software_id
    validation_response = await validate_model_id(id=model_software_id, config=config, request_style=request_style)
    if isinstance(validation_response, str):
        return False, f"Model with id {model_software_id} (associated with workflow definition) was not a valid model, error: {validation_response}."

    # modeller
    modeller = associations.modeller_id
    validation_response = await validate_person_id(id=modeller, config=config, request_style=request_style)
    if isinstance(validation_response, str):
        return False, f"Modeller with id {modeller} was not a valid person, error: {validation_response}."

    # optional(requesting_organisation)
    if associations.requesting_organisation_id:
        org_id = associations.requesting_organisation_id
        org_response = await validate_organisation_id(id=org_id, config=config, request_style=request_style)
        if isinstance(org_response, str):
            return False, f"Organisation with id {org_id} was not a valid organisation, error: {org_response}."

    # validate annotations
    # --------------------

    success, error = validate_annotations(
        workflow_template=workflow_response,
        model_run_record=record
    )

    if not success:
        return success, error

    # Seems to be valid, return such
    return True, None
