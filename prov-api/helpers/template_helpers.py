from __future__ import annotations
import collections
from itertools import chain
from fastapi.responses import FileResponse
from fastapi import HTTPException
from starlette.background import BackgroundTask
from ProvenaInterfaces.RegistryModels import ItemModelRunWorkflowTemplate, ItemDatasetTemplate, SeededItem, ItemDataset
from ProvenaInterfaces.ProvenanceModels import ModelRunRecord, TemplatedDataset, DatasetType, AssociationInfo
# from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.AsyncJobModels import *
from dataclasses import dataclass
from dependencies.dependencies import User
from helpers.entity_validators import validate_model_run_workflow_template, validate_dataset_template_id, validate_datastore_id, RequestStyle
from helpers.time_helpers import iso_to_epoch, epoch_to_iso
from helpers.job_api_helpers import fetch_job_by_id_admin
from typing import Any, Tuple, List, Dict, Optional, ClassVar, Union
import random
import os
from config import Config
import re
import uuid
from io import StringIO
import csv


# prefix all system only fields with an underscore
TEMPLATE_INTERNAL_PREFIX: str = "_"
ANNOTATION_PREFIX = "annotation: "


def duplicates(my_list: List[str]) -> List[str]:
    # Use collections counter object to get unique list of the inputted items
    # and the fre of each to check for duplicates and return any :).
    return [x for x, count in collections.Counter(my_list).items() if count > 1]


def has_duplicates(my_list: List[str]) -> bool:
    return len(duplicates(my_list=my_list)) > 0


def delete_file(filename: str) -> None:
    """
    delete_file

    Given a file name, will delete it from the current working
    directory. Used to cleanup after API file delivery.

    Parameters
    ----------
    filename : str
        The name of the file including file extension
    """
    os.remove(filename)


def generate_random_file_write(config: Config) -> Tuple[str, Any]:
    """
    generate_random_file 

    Generates a temp file to be used for file delivery. Tempfile library seemed
    buggy so we are implementing basic version. This is not mission critical
    functionality.

    Returns
    -------
    Tuple[str, Any]
        The name of the file, and the file itself
    """
    random_name = f"{config.TEMP_FILE_LOCATION}/config_temp{str(random.randint(1,100000))}.txt"
    f = open(random_name, 'w')
    return random_name, f


def generate_random_file_path(config: Config) -> str:
    """
    generate_random_file 

    Generates a temp file to be used for file delivery. Tempfile library seemed
    buggy so we are implementing basic version. This is not mission critical
    functionality.

    Returns
    -------
    str
        The name of the file
    """
    random_name = f"{config.TEMP_FILE_LOCATION}/template_temp{str(random.randint(1,100000))}.txt"
    return random_name


def generate_csv_file_content(headers: List[str], rows: List[List[str]]) -> List[List[str]]:
    return [headers] + rows


def write_csv_file_content(rows: List[List[str]], filepath: str) -> None:
    print(f"Writing {len(rows)} rows to template csv")
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print("Completed writing rows")


def generate_template_file(config: Config, headers: List[str], filename: str) -> FileResponse:
    # generate the CSV template document based on the headers
    path = generate_random_file_path(config)

    # generate content
    content = generate_csv_file_content(headers=headers, rows=[])

    # write content
    write_csv_file_content(rows=content, filepath=path)

    # Return the written file
    return FileResponse(
        path=path,
        filename=filename,
        background=BackgroundTask(delete_file, path)
    )


def generate_complete_template_file(config: Config, headers: List[str], rows: List[List[str]], filename: str) -> FileResponse:
    # generate the CSV template document based on the headers
    path = generate_random_file_path(config)

    # generate content
    content = generate_csv_file_content(headers, rows=rows)

    # write content
    write_csv_file_content(rows=content, filepath=path)

    # Return the written file
    return FileResponse(
        path=path,
        filename=filename,
        background=BackgroundTask(delete_file, path)
    )


def generate_workflow_template_flag(workflow_template_id: str, config: Config) -> str:
    # produce first column header which is a marker for the workflow template id
    return f"{TEMPLATE_INTERNAL_PREFIX}{config.WORKFLOW_TEMPLATE_MARKER_PREFIX} {workflow_template_id}"


def generate_workflow_template_flag_regex(config: Config) -> str:
    return re.escape(TEMPLATE_INTERNAL_PREFIX + config.WORKFLOW_TEMPLATE_MARKER_PREFIX) + r"[\s]{1}([^\s]*)"


def generate_headers_from_dataset_template(template: ItemDatasetTemplate, is_input: bool, config: Config, name: str) -> DatasetTemplateHeaderInfo:
    # general ID declaration header
    dec_header: str
    if is_input:
        dec_header = f"{config.INPUT_DATASET_TEMPLATE_PREFIX}{name} [template id: {template.id}]"
        # for each deferred resource, allow reference to a file path
        headers = list(
            map(lambda deferred:  config.INPUT_TEMPLATE_RESOURCE_PREFIX + deferred.key, template.deferred_resources))
    else:  # is output
        dec_header = f"{config.OUTPUT_DATASET_TEMPLATE_PREFIX}{name} [template id: {template.id}]"
        # for each deferred resource, allow reference to a file path
        headers = list(
            map(lambda deferred:  config.OUTPUT_TEMPLATE_RESOURCE_PREFIX + deferred.key, template.deferred_resources))

    # for each deferred resource, allow reference to a file path
    keys = list(
        map(lambda deferred: deferred.key, template.deferred_resources))

    return DatasetTemplateHeaderInfo(
        dataset_template_id=template.id,
        template_id_header=dec_header,
        deferred_resource_headers=headers,
        deferred_resource_keys=keys,
        is_input=is_input
    )


def check_match(pattern: re.Pattern[str], test: str) -> Optional[re.Match[str]]:
    if not isinstance(test, str):
        return None
    else:
        return pattern.match(test)


def derive_template_id(csv_rows: List[Dict[str, str]], config: Config) -> str:
    if len(csv_rows) == 0:
        raise HTTPException(
            status_code=400, detail="The provided CSV had no non header rows.")
    headers = list(csv_rows[0].keys())

    header_regex = generate_workflow_template_flag_regex(config)
    compiled = re.compile(header_regex)

    def check(header: str) -> Optional[re.Match[str]]:
        return check_match(compiled, header)

    matched_headers = list(
        filter(lambda match: match is not None, map(check, headers)))

    if len(matched_headers) == 0:
        raise HTTPException(
            status_code=400, detail="None of the provided headers matched the expected workflow template flag to identify the workflow template.")
    if len(matched_headers) > 1:
        raise HTTPException(
            status_code=400, detail="Multiple provided headers matched the expected workflow template flag to identify the workflow template.")

    assert len(matched_headers) == 1
    matched_flag = matched_headers[0]
    assert matched_flag is not None

    try:
        id_group: str = matched_flag.group(1)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"A header matched the workflow template ID regex but the first match group could not be used! Error {e}."
        )

    return id_group.strip()


@dataclass
class DatasetTemplateHeaderInfo():
    dataset_template_id: str
    template_id_header: str
    deferred_resource_headers: List[str]
    deferred_resource_keys: List[str]
    is_input: bool

    def compile(self) -> List[str]:
        return [self.template_id_header] + self.deferred_resource_headers

    def validate(self, headers: List[str]) -> None:
        for header in self.compile():
            assert header in headers, f"Expected dataset template header {header} not in provided headers."

    async def generate(self, data: Dict[str, str], request_style: RequestStyle, config: Config) -> TemplatedDataset:
        # get the dataset ID
        dataset_id = data[self.template_id_header]

        # get the dataset
        dataset = await validate_datastore_id(id=dataset_id, request_style=request_style, config=config)

        # throw respective errors
        if isinstance(dataset, str):
            raise HTTPException(
                status_code=400, detail=f"The provided workflow template contained a dataset id {dataset_id} which was invalid, error: {dataset}.")

        # all good
        assert isinstance(dataset, ItemDataset)

        # now check the paths for the deferred resources and create map
        resources: Dict[str, str] = {}
        for key, header in zip(self.deferred_resource_keys, self.deferred_resource_headers):
            path = data[header]
            assert path is not None and path != ""
            resources[key] = path

        return TemplatedDataset(
            dataset_template_id=self.dataset_template_id,
            dataset_id=dataset_id,
            dataset_type=DatasetType.DATA_STORE,
            resources=resources if len(resources) > 0 else None
        )

    def fillout(self, model_run_record: ModelRunRecord) -> List[str]:
        """
             dataset_template_id: str
             template_id_header: str
             deferred_resource_headers: List[str]

             def compile(self) -> List[str]:
                 return [self.template_id_header] + self.deferred_resource_headers
        """
        output_entries: List[str] = []

        # get the dataset ID for the specified template
        template_id = self.dataset_template_id

        # derive input vs output
        if self.is_input:
            entries = model_run_record.inputs
        else:
            entries = model_run_record.outputs

        label = "input" if self.is_input else "output"

        found = False
        record: Optional[TemplatedDataset] = None
        for entry in entries:
            if entry.dataset_template_id == template_id:
                found = True
                record = entry
                break
        if not found:
            raise HTTPException(
                status_code=400,
                detail=f"No {label} found in model run record for dataset template: {template_id}."
            )

        # type hint
        assert record is not None
        # add the dataset ID to the output entries
        output_entries.append(record.dataset_id)

        # add the deferred resources
        for key in self.deferred_resource_keys:
            if record.resources is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected deferred resource: {key} but was not found in model run record."
                )

            val = record.resources.get(key)
            if val is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected deferred resource: {key} but was not found in model run record."
                )

            output_entries.append(val)

        return output_entries


@dataclass
class GenericTemplateHeaderInfo():
    display_name_header: str
    model_version_header: str
    description_header: str
    agent_id_header: str
    study_id_header: str
    # Removing requesting organisation for v1
    # requesting_org_id_header: str
    start_time_header: str
    end_time_header: str

    def validate(self, headers: List[str]) -> None:
        for header in self.compile():
            assert header in headers, f"Expected header '{header}' not in headers!"

    def compile(self) -> List[str]:
        # order must match fillout order
        return [self.display_name_header,
                self.description_header,
                self.model_version_header,
                self.agent_id_header,
                self.study_id_header,
                self.start_time_header,
                self.end_time_header]

    def get_model_version(self, data: Dict[str, str]) -> Optional[str]:
        val = data.get(self.model_version_header)

        if val == "":
            return None

        return val

    def get_display_name(self, data: Dict[str, str]) -> str:
        val = data[self.display_name_header]
        assert val is not None
        assert val is not "", f"Expected display name to be non-empty string."
        return val

    def get_description(self, data: Dict[str, str]) -> str:
        val = data[self.description_header]
        assert val is not None
        assert val is not "", f"Expected description to be non-empty string."
        return val

    def get_agent_id(self, data: Dict[str, str]) -> str:
        val = data[self.agent_id_header]
        assert val is not None
        return val

    def get_study_id(self, data: Dict[str, str]) -> Optional[str]:
        val = data[self.study_id_header]

        if val == "":
            return None

        # can be none
        return val

    def get_start_time(self, data: Dict[str, str]) -> int:
        val = data[self.start_time_header]
        assert val is not None
        return iso_to_epoch(val)

    def get_end_time(self, data: Dict[str, str]) -> int:
        val = data[self.end_time_header]
        assert val is not None
        return iso_to_epoch(val)

    def fillout(self, model_run_record: ModelRunRecord) -> List[str]:
        output_entries: List[str] = []

        # Display name
        output_entries.append(model_run_record.display_name)

        # description
        output_entries.append(model_run_record.description or "")

        # model version
        output_entries.append(model_run_record.model_version or "")

        # agent id
        output_entries.append(model_run_record.associations.modeller_id)

        # study
        output_entries.append(model_run_record.study_id or "")

        # start/end time
        output_entries.append(epoch_to_iso(model_run_record.start_time))
        output_entries.append(epoch_to_iso(model_run_record.end_time))

        return output_entries


@dataclass
class AnnotationTemplateHeaderInfo():
    required_annotations: List[str]
    optional_annotations: List[str]

    @staticmethod
    def convert_to_header(annotation: str) -> str:
        return ANNOTATION_PREFIX + annotation

    def validate(self, headers: List[str]) -> None:
        for required in self.required_annotations:
            assert AnnotationTemplateHeaderInfo.convert_to_header(
                required) in headers, f"CSV has no header for {required} annotation."
        for optional in self.optional_annotations:
            assert AnnotationTemplateHeaderInfo.convert_to_header(
                optional) in headers, f"CSV has no header for {optional} annotation."

    def compile(self) -> List[str]:
        return [AnnotationTemplateHeaderInfo.convert_to_header(ann) for ann in self.required_annotations + self.optional_annotations]

    def generate(self, data: Dict[str, str]) -> Optional[Dict[str, str]]:
        annotations: Dict[str, str] = {}

        # Required annotations
        for req in self.required_annotations:
            header = AnnotationTemplateHeaderInfo.convert_to_header(req)
            val = data[header]
            if val is None or val == "":
                raise HTTPException(
                    status_code=400,
                    detail=f"Required annotation with key {req} was either empty or None."
                )
            annotations[req] = val

        # Optional annotations
        for opt in self.optional_annotations:
            header = AnnotationTemplateHeaderInfo.convert_to_header(opt)
            value = data[header]
            if value is not None and value != "":
                annotations[opt] = value

        return annotations if len(annotations) > 0 else None

    def fillout(self, model_run_record: ModelRunRecord) -> List[str]:
        output_entries: List[str] = []
        annotations = model_run_record.annotations

        if annotations is None:
            if len(self.required_annotations) > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model run record had no annotations, but template had required annotations."
                )
            else:
                # Return empty entries
                return ["" for _ in self.required_annotations + self.optional_annotations]

        for req in self.required_annotations:
            if req in annotations:
                val = annotations[req]
                output_entries.append(val)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Workflow template expected annotation with key {req} but it was not provided in the model run record."
                )
        for opt in self.optional_annotations:
            if opt in annotations:
                val = annotations[opt]
                output_entries.append(val)
            else:
                output_entries.append("")

        return output_entries


@dataclass
class JobTemplateHeaderInfo():
    job_id_header: ClassVar[str] = TEMPLATE_INTERNAL_PREFIX + "job_id"
    job_status_header: ClassVar[str] = TEMPLATE_INTERNAL_PREFIX + "job_status"
    record_id_header: ClassVar[str] = TEMPLATE_INTERNAL_PREFIX + \
        "model_run_record_id"
    error_header: ClassVar[str] = TEMPLATE_INTERNAL_PREFIX + "error_info"

    status_headers: ClassVar[List[str]] = [
        job_id_header,
        job_status_header,
        record_id_header,
        error_header
    ]

    def validate(self, headers: List[str]) -> None:
        for required in self.status_headers:
            assert required in headers, f"CSV is missing expected status header {required}."

    def compile(self) -> List[str]:
        return self.status_headers

    def fillout(self, model_run_record: ModelRunRecord) -> List[str]:
        # compile outputs
        return ["" for _ in self.status_headers]

    def fillout_status(self, job: JobStatusTable) -> List[str]:
        # compile outputs
        outputs: List[str] = []

        record_id = ""
        error_info = (job.info or "") if job.status == JobStatus.FAILED else ""
        # Parse the result type
        if job.result is not None:
            result = ProvLodgeModelRunResult.parse_obj(job.result)
            record_id = result.record.id

        # job id
        outputs.append(job.session_id)

        # job status
        outputs.append(job.status)

        # model run record id
        outputs.append(record_id)

        # error
        outputs.append(error_info)

        return outputs

    def exists(self, data: Dict[str, Any], config: Config) -> Tuple[bool, Optional[str]]:
        # does this record already exist/has already been lodged?

        # raises an exception if the job id is present but it is unparsable

        # if there is a job ID which is not an empty string then return true
        # else false - validated so we know it exists

        # This should not occur, but good to double check
        if self.job_id_header not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing job_id header - validation failed."
            )

        job_id = data[self.job_id_header]

        if job_id is not None and job_id != "":
            # parse as uuid
            try:
                uuid_obj = uuid.UUID(job_id, version=4)
            except:
                raise HTTPException(
                    status_code=400,
                    detail=f"Provided ({job_id = }) was not a valid UUID4 identitifer."
                )

            # now check that the job exists
            try:
                # TODO ASYNC
                # Use the jobs infra instead
                item = fetch_job_by_id_admin(
                    session_id=job_id,
                    config=config
                )
                if item is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"The ({job_id = }) is a valid UUID4 identifier but does not exist in the job status database."
                    )
                else:
                    return True, job_id
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during attempted validation of {job_id = }, error: {e}."
                )

        return False, None


@dataclass
class TemplateHeaderInfo():
    workflow_flag_header: str
    generic_headers: GenericTemplateHeaderInfo
    input_dataset_headers: List[DatasetTemplateHeaderInfo]
    output_dataset_headers: List[DatasetTemplateHeaderInfo]
    annotation_headers: AnnotationTemplateHeaderInfo
    job_headers: JobTemplateHeaderInfo

    def validate(self, headers: List[str]) -> None:
        self.generic_headers.validate(headers)
        for input_ds in self.input_dataset_headers:
            input_ds.validate(headers)
        for output_ds in self.output_dataset_headers:
            output_ds.validate(headers)
        self.annotation_headers.validate(headers)
        self.job_headers.validate(headers)
        assert self.workflow_flag_header in headers

    def compile(self) -> List[str]:
        return [self.workflow_flag_header] + self.generic_headers.compile() + \
            list(chain(*[o.compile() for o in self.input_dataset_headers])) + \
            list(chain(*[o.compile() for o in self.output_dataset_headers])) + \
            self.annotation_headers.compile() + \
            self.job_headers.compile()

    def warn_extra(self, headers: List[str]) -> List[str]:
        """
        warn_extra 

        Given a list of headers in a CSV, uses the compile method to find CSV
        headers which are not part of expected template.

        Parameters
        ----------
        headers : List[str]
            The list of CSV headers

        Returns
        -------
        List[str]
            A list of headers not in the expected template
        """
        return list(
            set(headers) - set(self.compile())
        )

    def fillout_no_status(self, model_run_record: ModelRunRecord) -> List[str]:
        return [""] + self.generic_headers.fillout(model_run_record) + \
            list(chain(*[o.fillout(model_run_record) for o in self.input_dataset_headers])) + \
            list(chain(*[o.fillout(model_run_record) for o in self.output_dataset_headers])) + \
            self.annotation_headers.fillout(model_run_record) + \
            self.job_headers.fillout(model_run_record)

    def fillout_with_status(self, model_run_record: ModelRunRecord, job: JobStatusTable) -> List[str]:
        return [""] + self.generic_headers.fillout(model_run_record) + \
            list(chain(*[o.fillout(model_run_record) for o in self.input_dataset_headers])) + \
            list(chain(*[o.fillout(model_run_record) for o in self.output_dataset_headers])) + \
            self.annotation_headers.fillout(model_run_record) + \
            self.job_headers.fillout_status(job)


async def generate_csv_template_header_info(workflow_template_id: str, request_style: RequestStyle, config: Config) -> TemplateHeaderInfo:
    # lookup the workflow template ID
    workflow_template = await validate_model_run_workflow_template(id=workflow_template_id, request_style=request_style, config=config)

    if isinstance(workflow_template, str):
        raise HTTPException(
            status_code=400, detail=f"The provided workflow template ID was invalid, error: {workflow_template}.")
    if isinstance(workflow_template, SeededItem):
        raise HTTPException(
            status_code=400, detail=f"The provided workflow template ID was a seed item.")

    # we now have a complete workflow template
    assert isinstance(workflow_template, ItemModelRunWorkflowTemplate)

    # get the input/output template ids
    input_template_ids = list(
        map(lambda t: t.template_id, workflow_template.input_templates))
    output_template_ids = list(
        map(lambda t: t.template_id, workflow_template.output_templates))

    async def resolve_template(template_id: str) -> ItemDatasetTemplate:
        # lookup and get object, error or seed item
        resolved = await validate_dataset_template_id(id=template_id, request_style=request_style, config=config)

        # throw respective errors
        if isinstance(resolved, str):
            raise HTTPException(
                status_code=400, detail=f"The provided workflow template contained a dataset template id {template_id} which was invalid, error: {resolved}.")
        if isinstance(resolved, SeededItem):
            raise HTTPException(
                status_code=400, detail=f"The provided workflow template contained a seeded dataset template with id {template_id}.")

        # all good
        assert isinstance(resolved, ItemDatasetTemplate)
        return resolved

    # for each, resolve the actual template
    resolved_input_templates = [await resolve_template(id) for id in input_template_ids]
    resolved_output_templates = [await resolve_template(id) for id in output_template_ids]

    # generate all input/output headers
    input_headers: List[DatasetTemplateHeaderInfo] = list(map(
        lambda t: generate_headers_from_dataset_template(template=t, config=config, is_input=True, name=t.display_name), resolved_input_templates))
    output_headers: List[DatasetTemplateHeaderInfo] = list(map(
        lambda t: generate_headers_from_dataset_template(template=t, config=config, is_input=False, name=t.display_name), resolved_output_templates))

    # now generate annotation headers
    if workflow_template.annotations is not None:
        required = workflow_template.annotations.required
        optional = workflow_template.annotations.optional
    else:
        required = []
        optional = []

    annotations = AnnotationTemplateHeaderInfo(
        required_annotations=required,
        optional_annotations=optional
    )

    # produce first column header which is a marker for the workflow template id
    mark_header = generate_workflow_template_flag(
        workflow_template_id=workflow_template_id,
        config=config
    )

    # generic headers
    generic = GenericTemplateHeaderInfo(
        model_version_header=config.TEMPLATE_MODEL_VERSION_HEADER,
        display_name_header=config.TEMPLATE_DISPLAY_NAME_HEADER,
        description_header=config.TEMPLATE_DESCRIPTION_HEADER,
        agent_id_header=config.TEMPLATE_AGENT_HEADER,
        study_id_header=config.STUDY_HEADER,
        start_time_header=config.TEMPLATE_START_TIME_HEADER,
        end_time_header=config.TEMPLATE_END_TIME_HEADER,
    )

    return TemplateHeaderInfo(
        workflow_flag_header=mark_header,
        generic_headers=generic,
        input_dataset_headers=input_headers,
        output_dataset_headers=output_headers,
        annotation_headers=annotations,
        job_headers=JobTemplateHeaderInfo()
    )


async def generate_model_run_record_from_template(user: User, workflow_template_id: str, header_info: TemplateHeaderInfo, data: Dict[str, str], config: Config) -> Tuple[Union[ModelRunRecord, str], bool]:
    # check if it exists
    exists, possible_job_id = header_info.job_headers.exists(
        data=data, config=config)

    # if it exists, we have a job id - no need to fully convert the record
    if exists:
        assert possible_job_id
        return possible_job_id, True

    # standard request type
    request_style = RequestStyle(user_direct=user, service_account=None)

    print("Generating inputs")
    inputs = [await info.generate(data=data, request_style=request_style, config=config)
              for info in header_info.input_dataset_headers]
    print("Generating outputs")
    outputs = [await info.generate(data=data, request_style=request_style, config=config)
               for info in header_info.output_dataset_headers]
    annotations = header_info.annotation_headers.generate(data=data)
    start_time = header_info.generic_headers.get_start_time(data=data)
    end_time = header_info.generic_headers.get_end_time(data=data)
    display_name = header_info.generic_headers.get_display_name(data=data)
    model_version = header_info.generic_headers.get_model_version(data=data)
    description = header_info.generic_headers.get_description(data=data)
    agent_id = header_info.generic_headers.get_agent_id(data=data)
    study_id = header_info.generic_headers.get_study_id(data=data)
    # Removing requesting organisation for v1
    # org_id = header_info.generic_headers.get_requesting_org_id(data=data)

    # the record is new, and it is valid
    return (ModelRunRecord(
        workflow_template_id=workflow_template_id,
        model_version=model_version,
        inputs=inputs,
        outputs=outputs,
        annotations=annotations,
        display_name=display_name,
        description=description,
        associations=AssociationInfo(
            modeller_id=agent_id,
            # Removing requesting organisation for v1
            # requesting_organisation_id=org_id
            # requesting_organisation_id=None
        ),
        study_id=study_id,
        start_time=start_time,
        end_time=end_time
    ), False)


def generate_csv_entry_from_model_run_record_with_status(
    template_info: TemplateHeaderInfo,
    model_run_record: ModelRunRecord,
    job: JobStatusTable,
) -> List[str]:
    return template_info.fillout_with_status(
        model_run_record=model_run_record,
        job=job
    )


def duplicate_headers_in_file(file_contents: str) -> List[str]:
    """
    duplicate_headers_in_file 

    Reads file contents (string) as a CSV using the inbuilt CSV reader library
    and checks for duplicates in the header row.

    Parameters
    ----------
    file_contents : str
        The decoded contents of the file

    Returns
    -------
    List[str]
        The list of duplicates, if any. 

        No duplicates <-> []
    """

    return duplicates(get_headers_list(file_contents))


def get_headers_list(file_contents: str) -> List[str]:
    return next(csv.reader(StringIO(file_contents)))
