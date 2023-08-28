from io import StringIO
from typing import Dict, List
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, user_general_dependency, admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from config import get_settings, Config
from helpers.template_helpers import *
from SharedInterfaces.SharedTypes import Status
from SharedInterfaces.AsyncJobModels import *
from SharedInterfaces.ProvenanceAPI import ConvertModelRunsResponse
from csv import DictReader
from helpers.job_api_helpers import fetch_all_jobs_by_batch_id

router = APIRouter()


@router.get("/generate_template/csv", operation_id="generate_template_csv")
async def generate_csv_template(
    workflow_template_id: str,
    roles: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> FileResponse:

    request_style = RequestStyle(
        user_direct=roles.user, service_account=None)
    # get the header info

    header_info = await generate_csv_template_header_info(
        workflow_template_id=workflow_template_id,
        config=config,
        request_style=request_style
    )
    # compile into a list of headers deterministically
    headers = header_info.compile()

    dupes = duplicates(headers)
    if len(dupes) > 0:
        raise HTTPException(
            status_code=500, detail=f"Cannot generate CSV template with duplicate headers: {dupes}")

    # now generate the required headers for each template
    return generate_template_file(config=config, headers=headers, filename=f"test.csv")


@router.post("/convert_model_runs/csv", response_model=ConvertModelRunsResponse, operation_id="convert_model_runs_csv")
async def convert_model_runs_csv(
    csv_file: UploadFile,
    roles: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> ConvertModelRunsResponse:
    # get the contents of the CSV file
    try:
        # read file contents as string - utf-8 decoding
        file_contents = (await csv_file.read()).decode("utf-8")

        # check for possible duplicates in file contents
        duplicates = duplicate_headers_in_file(file_contents=file_contents)
        if len(duplicates) != 0:
            raise Exception(
                f"Duplicate headers are not allowed. Detected duplicates: {duplicates}.")

        # Read the rows using a dictionary reader
        reader = DictReader(StringIO(file_contents))
        rows: List[Dict[str, str]] = list(reader)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"An error occurred while parsing the uploaded csv file - are you sure it is valid? Exception: {e}.")

    # now derive the workflow template ID from this CSV
    workflow_template_id = derive_template_id(csv_rows=rows, config=config)

    # standard request style
    request_style = RequestStyle(
        user_direct=roles.user, service_account=None)

    # follow the same process as generating the template to 1) validate the template and children 2) get the list of headers
    template_header_info = await generate_csv_template_header_info(
        workflow_template_id=workflow_template_id,
        request_style=request_style,
        config=config
    )

    # now check the headers against expected header info
    assert len(rows) > 0, f"Empty CSV provided"
    headers = list(rows[0].keys())

    try:
        template_header_info.validate(headers)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Header validation error in CSV: {e}")

    warnings: List[str] = []
    extras = template_header_info.warn_extra(headers)
    warnings.extend(
        [f"Extra column with header '{extra}' provided, ignoring" for extra in extras])

    def sanitize_row_data(data: Dict[str, str]) -> Dict[str, str]:
        """
        sanitize_row_data

        Strips any trailing or leading whitespace from the cells before validation

        Parameters
        ----------
        data : Dict[str, str]
            The csv entry mapping headers -> data

        Returns
        -------
        Dict[str, str]
            The output version
        """
        return {key: string_value.strip() for key, string_value in data.items()}

    # construct model run records - strip whitespace from all entries before
    # running the generate func
    try:
        record_or_job_id_and_exist = []
        for row_num, row in enumerate(rows):
            record_or_job_id_and_exist.append(
                await generate_model_run_record_from_template(
                    user=roles.user,
                    workflow_template_id=workflow_template_id,
                    header_info=template_header_info,
                    data=sanitize_row_data(row),
                    config=config
                )
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"There was an error while converting the CSV row for model run #{row_num+1} into a model run record, exception: {e}.")

    # return the model run records
    new_records: List[ModelRunRecord] = []
    existing_records: List[str] = []

    for rec_or_job_id, exists in record_or_job_id_and_exist:
        if exists:
            assert isinstance(rec_or_job_id, str)
            existing_records.append(rec_or_job_id)
        else:
            assert isinstance(rec_or_job_id, ModelRunRecord)
            new_records.append(rec_or_job_id)

    return ConvertModelRunsResponse(
        status=Status(
            success=True, details=f"Successfully generated model run records. There were {len(warnings)} warnings."),
        new_records=new_records,
        existing_records=existing_records,
        warnings=warnings
    )


@router.get("/regenerate_from_batch/csv", operation_id="regenerate_from_batch_csv")
async def regenerate_from_batch_csv(
    batch_id: str,
    roles: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> FileResponse:
    # lookup the batch ID in batch table ID by user username
    batch_jobs = await fetch_all_jobs_by_batch_id(
        batch_id=batch_id, token=roles.user.access_token, config=config)

    # check that the jobs are model run lodge type
    for job in batch_jobs:
        if job.job_sub_type != JobSubType.MODEL_RUN_PROV_LODGE:
            raise HTTPException(
                status_code=400,
                detail=f"The specified batch ID {batch_id} contained jobs with non model run lodge job types."
            )

    # parse the specific type
    try:
        parsed_payloads = [ProvLodgeModelRunPayload.parse_obj(
            item.payload) for item in batch_jobs]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"The specified batch ID {batch_id} contained jobs which could not be parsed as valid job payloads. Error: {e}."
        )

    # check that all workflow templates are the same
    template_set = set(
        [job.record.workflow_template_id for job in parsed_payloads])
    if len(template_set) > 1:
        raise HTTPException(
            status_code=400,
            detail=f"The specified batch ID {batch_id} contained jobs with more than one workflow template IDs."
        )

    workflow_template_id: str = template_set.pop()

    # generate the csv template information from the workflow template ID
    header_info = await generate_csv_template_header_info(
        workflow_template_id=workflow_template_id,
        request_style=RequestStyle(
            user_direct=roles.user, service_account=None),
        config=config
    )

    headers = header_info.compile()
    rows = [
        generate_csv_entry_from_model_run_record_with_status(
            template_info=header_info,
            model_run_record=parsed.record,
            job=job
        ) for job, parsed in zip(batch_jobs, parsed_payloads)
    ]

    # now generate the required headers for each template
    return generate_complete_template_file(config=config, headers=headers, rows=rows, filename=f"model_runs.csv")
