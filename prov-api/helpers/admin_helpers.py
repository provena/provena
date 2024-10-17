from fastapi import HTTPException
from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.SharedTypes import Status
from config import Config
from helpers.validate_model_run_record import validate_model_run_record, validate_model_run_workflow_template, RequestStyle
from dependencies.dependencies import User
from helpers.async_requests import async_post_request
from helpers.prov_connector import Neo4jGraphManager
from helpers.prov_helpers import model_run_to_graph
import json


async def list_model_run_records_from_registry(
    config: Config,
    user: User
) -> List[ItemModelRun]:
    """
    list_model_run_records_from_registry

    Accesses the registry and lists all of the model run records

    Repeatedly queries

    Parameters
    ----------
    config : Config
        The config

    Returns
    -------
    List[ItemModelRun]
        The list of complete item model runs

    Raises
    ------
    HTTPException
        Http exception raised due to various error conditions
    """

    # get service token
    token = user.access_token

    more_items: bool = True
    pagination_key: Optional[PaginationKey] = None

    items: List[ItemModelRun] = []
    while more_items:
        # list endpoint - get complete records only
        endpoint = config.registry_api_endpoint + "/registry/activity/model_run/list"
        payload = json.loads(SubtypeListRequest(
            pagination_key=pagination_key,
            filter_by=SubtypeFilterOptions(
                record_type=QueryRecordTypes.COMPLETE_ONLY)
        ).json())

        # Make request
        try:
            fetch_response = await async_post_request(
                endpoint=endpoint,
                token=token,
                params={},
                json_body=payload
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")

        # check the status of the response
        status_code = fetch_response.status_code
        if status_code != 200:
            # try and get details then raise HTTPException
            try:
                detail = fetch_response.json()['detail']
                raise HTTPException(
                    status_code=500,
                    detail=f"Registry API responded with non 200 code: {status_code}. Error: {detail}"
                )

            except:  # unable to get details
                raise HTTPException(
                    status_code=500,
                    detail=f"Registry API responded with non 200 code: {status_code}. "
                )

        # 200 code meaning that parse model will be valid
        try:
            model_run_list_response: ModelRunListResponse = ModelRunListResponse.parse_obj(
                fetch_response.json())
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Tried to parse successful response from registry API model run list endpoint but failed. Parse error {e}."
            )

        # We now have a parsed model response
        if model_run_list_response.status.success:
            if model_run_list_response.items:
                items.extend(model_run_list_response.items)
                pagination_key = model_run_list_response.pagination_key
                if pagination_key is not None:
                    more_items = True
                else:
                    more_items = False
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Response from registry API was successful but had no item property!"
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Response from registry API was unsuccessful, error: {model_run_list_response.status.details}."
            )
    return items


async def store_existing_record(
    registry_record: ItemModelRun,
    validate_record: bool,
    config: Config,
    user: User,
) -> StatusResponse:
    """
    store_existing_record

    An admin only endpoint which enables the reupload/storage of an existing
    completed provenance record.

    Optionally, the record can also be revalidated.

    It might be wise to start with an empty graph before running this command
    however it should work regardless since the properties will be merged on
    existing nodes.

    Parameters
    ----------
    registry_record : ItemModelRun
        The completed registry record for the model run
    validate_record : bool, optional
        Should the ids in the payload be validated?, by default True

    Returns
    -------
    StatusResponse
        A status response

    Raises
    ------
    HTTPException
        Various HTTP exceptions if errors occur
    """
    # ===========================
    # Validate record if required
    # ===========================

    # standard user based validation
    request_style = RequestStyle(user_direct=user, service_account=None)

    #
    if validate_record:
        valid, error_message = await validate_model_run_record(record=registry_record.record, request_style=request_style, config=config)

        if not valid:
            assert error_message
            raise HTTPException(
                status_code=400,
                detail=f"Failed to validate an entity's ID in the record, error: {error_message}."
            )

    # Extract the existing handle
    handle_id = registry_record.id

    # ==========================================================
    # Convert fully identified record into python-prov document
    # Integrate handle IDs into prov document
    # ==========================================================

    # resolve the workflow definition (and implicitly validate)
    workflow_response = await validate_model_run_workflow_template(
        id=registry_record.record.workflow_template_id,
        config=config,
        request_style=request_style
    )
    if isinstance(workflow_response, str):
        raise HTTPException(
            status_code=400,
            detail=f"Workflow definition with id: {registry_record.record.workflow_template_id} failed validation with error: {workflow_response}."
        )
    if isinstance(workflow_response, SeededItem):
        raise HTTPException(
            status_code=400,
            detail=f"Workflow definition with id: {registry_record.record.workflow_template_id} was an incomplete seeded item!."
        )

    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    try:
        graph = model_run_to_graph(
            model_record=registry_record.record,
            record_id=handle_id,
            workflow_template=workflow_response
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Error occurred while producing the provenance document with an existing handle: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while producing the provenance document with an existing handle: {e}"
        )

    # ==========================================
    # Upload provenance record into graph store
    #
    # This is an additive merge
    # ==========================================

    manager = Neo4jGraphManager(config=config)
    manager.merge_add_graph_to_db(graph)

    return StatusResponse(
        status=Status(
            success=True, details=f"Successfully re-lodged item."),
    )
