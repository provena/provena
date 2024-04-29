from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from ProvenaInterfaces.AuthAPI import *
from helpers.request_table_helpers import *
from helpers.email_helpers import *
import traceback
from config import Config, get_settings

router = APIRouter(
    prefix="/admin"
)


@router.get("/all-pending-request-history", response_model=AccessRequestList, operation_id="get_all_pending_requests")
async def all_pending_request_history(
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> AccessRequestList:
    """    all_pending_request_history
        Given admin read permissions, pulls all entries in the access request table.

        Arguments
        ----------

        Returns
        -------
         : AccessRequestList
            list of access request items

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_all_access_request_entries(config=config)

    # Filter for pending
    pending_items = list(filter(lambda item: item.status ==
                         RequestStatus.PENDING_APPROVAL, items))

    # package and return
    return AccessRequestList(items=pending_items)


@router.get("/all-request-history", response_model=AccessRequestList, operation_id="get_all_requests")
async def all_request_history(
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> AccessRequestList:
    """    all_request_history
        Given admin read permissions, pulls all entries in the access request table.

        Arguments
        ----------

        Returns
        -------
         : AccessRequestList
            list of access request items

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_all_access_request_entries(config=config)

    # package and return
    return AccessRequestList(items=items)


@router.get("/user-pending-request-history", response_model=AccessRequestList, operation_id="get_all_pending_requests_for_user")
async def user_pending_request_history(
    username: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> AccessRequestList:
    """    user_pending_request_history
        Given admin read permissions will pull the pending requests of
        a specified username.

        Arguments
        ----------
        username : str
            The username to pull history for.

        Returns
        -------
         : AccessRequestList
            list of access request items

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_access_request_entries(username, config=config)

    # Filter for pending
    pending_items = list(filter(lambda item: item.status ==
                         RequestStatus.PENDING_APPROVAL, items))

    # package and return
    return AccessRequestList(items=pending_items)


@router.get("/user-request-history", response_model=AccessRequestList, operation_id="get_all_requests_for_user")
async def user_request_history(
    username: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> AccessRequestList:
    """    user_request_history
        Given admin read permissions will pull the request history of
        a specified username.

        Arguments
        ----------
        username : str
            The username to pull history for.

        Returns
        -------
         : AccessRequestList
            list of access request items

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_access_request_entries(username, config=config)

    # package and return
    return AccessRequestList(items=items)


@router.post("/add-note", response_model=Status, operation_id="add_note")
async def add_note(
    note_information: RequestAddNote,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> Status:
    # Retrieve request
    item = get_request_entry(
        username=note_information.username,
        request_id=note_information.request_id,
        config=config
    )

    # Check if not present
    if not item:
        return Status(success=False, details="Could not find item in table.")

    # Update timestamp
    touch_record_timestamp(item)

    # Add notes if required
    append_note_to_item(item, note_information.note)

    # update record
    write_access_request_entry(item, config=config)

    # package and return
    return Status(success=True, details=f"Added note.")


@router.post("/change-request-state", response_model=ChangeStateStatus, operation_id="change_request_state")
async def change_request_state(
    # Post form
    change_request: AccessRequestStatusChange,
    # Query string
    send_email_alert: Optional[bool] = False,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> ChangeStateStatus:
    """    change_request_state
        For the specified user/id etc will update the entry in the 
        table of access requests with the new state and the desired 
        note if included.

        If desired, an email will be sent to the specified user email 
        as per the request information.

        Arguments
        ----------
        change_request : AccessRequestStatusChange
            The change request object - see models.py 
        send_email_alert : Optional[bool]
            Should the user be sent an email which updates them as to the 
            status change.

        Returns
        -------
         : ChangeStateStatus
            Success if updated, false and message otherwise

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Unpack the model inputs
    username = change_request.username
    request_id = change_request.request_id
    desired_state = change_request.desired_state
    # optional
    additional_note = change_request.additional_note

    # Retrieve request
    item = get_request_entry(
        username=username, request_id=request_id, config=config)

    # Check if not present
    if not item:
        state_change = Status(
            success=False, details="Could not find item in table.")
        email_alert = Status(
            success=False, details="Could not find item in table.")
        return ChangeStateStatus(state_change=state_change, email_alert=email_alert)

    # Store original state
    original_status = item.status

    if item.status == desired_state:
        state_change = Status(
            success=True, details="Status was already matching - no update applied.")
        email_alert = Status(
            success=True, details="Status was already matching - no update applied.")
        return ChangeStateStatus(state_change=state_change, email_alert=email_alert)

    # Update status
    item.status = desired_state
    item.ui_friendly_status = REQUEST_STATUS_TO_USER_EXPLANATION[desired_state]

    # Update timestamp
    touch_record_timestamp(item)

    # Add notes if required
    if additional_note:
        append_note_to_item(item, additional_note)

    # update record
    write_access_request_entry(item, config=config)

    # Successful update
    state_change = Status(
        success=True, details=f"Updated status to {desired_state}.")

    # Do we need to send email?
    if not send_email_alert:
        # No email sent
        email_alert = Status(success=True, details=f"No email requested.")
    else:
        # Need email
        # but we should check this email appears valid
        email_address = item.email

        # No email present or None
        if not email_address or email_address == "":
            # No email address provided
            # Send failure
            email_alert = Status(
                success=False, details=f"No email address was present in the record so no email was sent.")

        # Check if the email is invalid
        elif not validate_email(email_address):
            email_alert = Status(
                success=False, details=f"Provided email: {email_address} appears to be invalid! No email sent.")
        else:
            # We have an email and it appears valid - send
            try:
                # Only send email if prod
                await send_status_change_email(
                    username=username,
                    email_address=email_address,
                    original_status=original_status,
                    new_status=desired_state,
                    request_entry=item,
                    config=config
                )
                email_alert = Status(
                    success=True, details=f"Update email dispatched successfully to {email_address}.")
            except Exception as e:
                traceback.print_exc()
                email_alert = Status(
                    success=False, details=f"Exception occurred when sending email to {email_address} - {e}. See API logs for more info.")
    return ChangeStateStatus(state_change=state_change, email_alert=email_alert)


@router.post("/delete-request", response_model=Status, operation_id="delete_request")
async def do_delete_request(
    delete_request: DeleteAccessRequest,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_admin_dependency)
) -> Status:
    """    delete_request
        Will delete record for specified username/id.

        Only allowed for sys admin admins - use with caution.

        Arguments
        ----------
        delete_request : DeleteAccessRequest
            Description of what to delete

        Returns
        -------
         : Status
            Success if deleted, will be true even if record doesn't exist

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Unpack the model inputs
    username = delete_request.username
    request_id = delete_request.request_id

    try:
        # Delete
        delete_request_entry(
            username=username, request_id=request_id, config=config)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete record: {e}"
        )

    return Status(success=True, details=f"Deleted record {request_id}")
