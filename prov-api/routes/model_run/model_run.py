from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, PROV_JOB_DISPATCHER_SERVICE_ROLE_NAME
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from SharedInterfaces.ProvenanceAPI import *
from helpers.workflows import *
from helpers.auth_helpers import *
from config import get_settings, Config

router = APIRouter()


@router.post("/register_complete", response_model=RegisterModelRunResponse, operation_id="register_complete_model_run")
async def register_model_run_complete(
    record: ModelRunRecord,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegisterModelRunResponse:
    """    register_model_run_complete
        Given the model run record object (schema/model) will:
        - validate the ids provided in the model 
            - Validate and retrieve the workflow definition
            - Validate the templates for the input and output datasets 
            - Validate that the provided datasets satisfy all templates
            - Validate that datasets provided through data store exist
        - mint a model run record in the registry (acting as prov-api proxy on proxy endpoints)
            - This uses the user's username so that the user correctly owns the record
        - produce a prov-o document reflecting the input model run record
        - update the model run record in the registry with the prov serialisation
          and other information 
        - lodge the model run record into the graph database store
        - update the record to lodged status 
        - return information including the handle id from the model run record

        Arguments
        ----------
        record : ModelRunRecord
            The model run record to lodge into the graph store and registry

        Returns
        -------
         : RegisterModelRunResponse
            The response including the handle id and record information

        Raises
        ------
        HTTPException
            If something goes wrong when validating the IDs returns a 400 error.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # no proxy - user direct
    request_style = RequestStyle(
        service_account=None, user_direct=roles.user)
    return await register_provenance(
        record=record,
        request_style=request_style,
        config=config,
    )

# This is a special route only for the prov job dispatcher to lodge on behalf of user


@router.post("/proxy/register_complete", response_model=RegisterModelRunResponse, operation_id="proxy_register_complete_model_run", include_in_schema=False)
async def proxy_register_model_run_complete(
    record: ModelRunRecord,
    username: Optional[str] = None,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegisterModelRunResponse:
    """    register_model_run_complete
        Same as above - but passes through the proxy username

        Arguments
        ----------
        record : ModelRunRecord
            The model run record to lodge into the graph store and registry
        username : str 
            The username to lodge on behalf of

        Returns
        -------
         : RegisterModelRunResponse
            The response including the handle id and record information

        Raises
        ------
        HTTPException
            If something goes wrong when validating the IDs returns a 400 error.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if username == "":
        raise HTTPException(
            status_code=400, detail=f"Cannot use empty username.")

    # check that this is the prov job dispatcher
    authorised = special_permission_check(user=roles.user, special_roles=[
        PROV_JOB_DISPATCHER_SERVICE_ROLE_NAME])

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"This proxy endpoint is not accesible by standard users. Not authorised."
        )

    # use proxy username - this uses the service account but calls downstream
    # proxy endpoints which check authorisation for username
    request_style = RequestStyle(
        service_account=ServiceAccountProxy(on_behalf_username=username, direct_service=False), user_direct=None)

    return await register_provenance(
        record=record,
        config=config,
        request_style=request_style
    )
