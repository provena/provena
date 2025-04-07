from dependencies.dependencies import admin_user_protected_role_dependency, get_user_cipher, ProtectedRole
from config import get_settings, Config
from KeycloakFastAPI.Dependencies import User
from ProvenaInterfaces.RegistryAPI import *
from fastapi import APIRouter, Depends
from helpers.admin_helpers import *

# Setup fastAPI router for this sub route
router = APIRouter()


@router.get("/export", response_model=RegistryExportResponse, operation_id="registry_admin_export")
async def export_items(
    user: User = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegistryExportResponse:
    """
    Provides a mechanism for admins to dump the current contents of the registry
    table without any validation/parsing.
    
    Now returns bundled items which correspond to the resource, auth and lock
    tables.

    Parameters
    ----------

    Returns
    -------
    RegistryExportResponse
        A status response including items in the payload.
    """
    # Use the admin helper function to dump all items
    items : List[BundledItem] = export_all_items(config)
    # Return success with length included in the status message
    return RegistryExportResponse(
        status=Status(
            success=True, details=f"Successfully exported {len(items)} items."),
        items=items
    )


@router.post("/import", response_model=RegistryImportResponse, operation_id="registry_admin_import")
async def import_items(
    import_request: RegistryImportRequest,
    user: User = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegistryImportResponse:
    """
    This admin only endpoint enables rapid restoration of items in into the
    registry table. 

    The import mode describes what kind of rules you want to apply about items. 

    The import_request contains the import mode, and other settings described
    below.

    Import mode - 

    ADD ONLY - will only add items - all items must be new and not exist in
    current registry.

    ADD_OR_OVERWRITE - will only add or overwrite existing items. This form of
    import will always validate as any items are valid.

    OVERWRITE_ONLY - all items must already exist in the registry, update will
    be applied with the new contents.

    SYNC_ADD_OR_OVERWRITE - sync mode is the same as ADD OR OVERRIDE but also
    enforces that there are no items in the current table which are not in the
    import items payload. If there are such items, this validation will fail -
    consider using the item below.

    SYNC_DELETION_ALLOWED - this will perform whatever is necessary to make the
    current registry table be identical to the provided items, including
    potentially deleting existing entries. USE WITH CAUTION. You must specify
    allow_entry_deletion explicitly to enable deletion.

    Parse items - this flag forces all items in the item payload to be parsed as
    their respective models. For example, if the list includes an item with a
    category/subtype but a body which doesn't parse as that type, then the
    import will fail.

    Allow entry deletion - this flag is only for use in the sync deletion
    allowed mode, and is a secondary defense against accidental deletion. Set to
    TRUE to enable deletion.

    Trial mode - this is a flag which determines whether a trial mode is being
    run. Trial mode will perform the entire process with the exception of
    actually writing any changes. True = trial mode. False = write changes.
    Default = True.

    Parameters
    ----------
    import_request : RegistryImportRequest
        The import request payload, as described above.

    Returns
    -------
    RegistryImportResponse
        Returns an import response which includes status + statistics.

    Raises
    ------
    http_exception
        Handled exception within import logic 
    HTTPException
        500 error if something else goes wrong
    """
    # use the admin helper function to crunch the numbers
    try:
        if import_request.parse_items:
            return import_parsed(import_request=import_request, config=config)
        else:
            return import_unparsed(import_request=import_request, config=config)
    # handled exception
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unhandled exception in import process : {e}.")


@router.post("/restore_from_table", response_model=RegistryImportResponse, operation_id="registry_admin_restore")
async def restore_from_table(
    restore_request: RegistryRestoreRequest,
    user: User = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegistryImportResponse:
    """
    Provides an admin only mechanism for copying/restoring the contents from
    another dynamoDB table into the currently active registry table. This
    endpoint does not create any new tables - it just uses the items from a
    restored table (e.g. from a backup) as inputs to an import operation against
    the current registry table.

    This is achieved by dumping the contents of the external table, then using
    the contents in the item payload to the import operation. The options
    provided in the import request here are propagated into the import request.

    For more information about the import options, see the /import endpoint and
    associated confluence documentation.

    NOTE the admin runtime must have AWS permissions to read from the specified
    AWS dynamoDB table. This table cannot be the same as the currently active
    registry table. If you are running the API locally then it is likely your
    local runtime will have these permissions if you are signed into AWS.
    However, if you are running this against a live API, you may need to update
    the CDK deployment or the Lambda API service role to have read only
    permissions into the specified table. You will get a 500 internal server
    error if the API cannot read from the table.

    Parameters
    ----------
    restore_request : RegistryRestoreRequest
        The restore request settings - these will be used when propagating the
        items from the external table.
    table_name : str
        The name of the external table

    Returns
    -------
    RegistryImportResponse
        Returns information about the import, including status and statistics.

    Raises
    ------
    http_exception
        If a handled error occurs during the import operation, will raise it
    HTTPException
        Otherwise a 500 error is returned with error details
    """

    # check that the import tables != the current tables
    table_names = restore_request.table_names
    if table_names.resource_table_name == config.registry_table_name or table_names.auth_table_name == config.auth_table_name or table_names.lock_table_name == config.lock_table_name:
        return RegistryImportResponse(
            status=Status(
                success=False,
                details=f"You supplied a table name which is the same as the current active registry table(s). This behaviour is not supported."
            ),
            trial_mode=restore_request.trial_mode
        )

    # dump the contents from the restore table, then run an import
    # with the specified settings and propagate the results

    # expects that we have read permissions into the specified
    # table! Will fail with 500 code if not.

    # Get the items from provided tables - this will consolidate!
    items = export_all_items_external_tables(
        table_names=table_names
    )

    # Run a parsed import on the specified items - this uses shared admin helper
    # functions since a restore is effectively an import with item contents from
    # an external table
    try:
        if restore_request.parse_items:
            return import_parsed(
                import_request=RegistryImportRequest(
                    items=items,
                    import_mode=restore_request.import_mode,
                    parse_items=restore_request.parse_items,
                    allow_entry_deletion=restore_request.allow_entry_deletion,
                    trial_mode=restore_request.trial_mode
                ),
                config=config)
        else:
            return import_unparsed(
                import_request=RegistryImportRequest(
                    items=items,
                    import_mode=restore_request.import_mode,
                    parse_items=restore_request.parse_items,
                    allow_entry_deletion=restore_request.allow_entry_deletion,
                    trial_mode=restore_request.trial_mode
                ),
                config=config)
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unhandled exception in import process : {e}.")


@router.post("/restore-prov-graph", response_model=ProvGraphRestoreResponse, operation_id="registry_admin_restore_prov_graph")
async def restore_prov_graph(
    restore_request: ProvGraphRestoreRequest,
    user_protected_role: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
) -> ProvGraphRestoreResponse:
    
    try:
        restore_response = await perform_graph_restore_helper(
            restore_request=restore_request,
            user=user_protected_role.user,
            config=config,
            user_cipher=user_cipher
        )
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unhandled exception in provenance graph restore : {e}.")
        
    return restore_response