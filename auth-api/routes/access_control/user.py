from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from SharedInterfaces.AuthAPI import *
from helpers.access_report_helpers import *
from helpers.email_helpers import *
from helpers.request_table_helpers import *
from config import Config, get_settings

router = APIRouter(
    prefix="/user"
)


@router.post("/request-change", response_model=AccessRequestResponse, operation_id="request_access_change")
async def request_access_change(
    access_report: AccessReport,
    send_email: Optional[bool] = True,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> AccessRequestResponse:
    """    request_access_change
        If you supply an access report which has differences to the current 
        token access levels, will send an email to the configured email addresses
        which details the differences in the authorisation.

        Adds an entry to the request access table which has the PENDING_APPROVAL 
        status and encodes the username/request ID.

        Will return a failure status if the user has a pending request which is too 
        recent based on the config minimum days value.

        Arguments
        ----------
        access_report : AccessReport
            The desired access levels in the form of an access report

        send_email : bool = True
            Should an alert email be sent?

        Returns
        -------
         : AccessRequestResponse
            Status saying whether or not the request was emailed successfully. 

        Raises
        ------
        HTTPException
            Raises 500 error if something goes wrong during process.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Create access report
    report = generate_report_from_user(user)

    # Compare access reports
    diff: AccessReport = find_access_report_changes(
        existing_access=report, desired_access=access_report)

    # Check that there are differences
    if len(diff.components) == 0:
        # If not, then don't return true status
        return AccessRequestResponse(
            status=Status(
                success=False,
                details="There were no differences between current access and desired access."
            )
        )

    # Check the status of the current user in the request backlog
    try:
        enable_request, reason = check_access_request(user, config=config)
    except HTTPException as e:
        # This is a valid fast API http error - just raise
        raise e
    except Exception as e:
        # This is probably an unexpected exception so wrap it as 500
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error when trying to get users\
                pending requests in request table: {e}"
        )

    if enable_request:
        # Generate entry to table
        entry = create_new_request_entry(
            user=user,
            notes=[],
            diff_report=diff,
            complete_report=report,
            config=config
        )
        try:
            write_access_request_entry(item=entry, config=config)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to write new pending registry item, aborting: {e}"
            )

        # Create request email with differences
        #if config.stage in ["OPSPROD", "PROD", "STAGE"] and send_email:
        # TODO revert!
        if config.stage in ["OPSPROD", "DEV", "PROD", "STAGE"] and send_email:
            try:
                # Only send email if prod
                await send_access_diff_email(
                    email_to=config.access_request_email_address, difference_report=diff, user=user, request_entry=entry, config=config)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to send request email, error: {e}.")

            # Return success and notify email sent
            return AccessRequestResponse(
                status=Status(
                    success=True,
                    details="Successfully requested an update to access and dispatched email."
                )
            )
        else:
            # Return success and notify no email sent
            return AccessRequestResponse(
                status=Status(
                    success=True,
                    details="Successfully requested an update to access. No email sent due to not being PROD."
                )
            )
    else:
        return AccessRequestResponse(
            status=Status(
                success=False,
                details=f"Failed due to user having unresolved requests, info: {reason}"
            )
        )


@router.get("/request-history", response_model=AccessRequestList, operation_id="get_requests")
async def get_full_user_request_history(
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> AccessRequestList:
    """    get_full_user_request_history
        For the current logged in user retrieves all of the entries in the 
        access request table. Note that the item format is directly mappable
        to the dynamodb entry.

        Arguments
        ----------

        Returns
        -------
         : AccessRequestList
            A list of access request entries in the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_access_request_entries(user.username, config=config)

    # package and return
    return AccessRequestList(items=items)


@router.get("/pending-request-history", response_model=AccessRequestList, operation_id="get_pending_requests")
async def get_pending_access_requests(
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> AccessRequestList:
    """    get_pending_access_requests
        For the current logged in user retrieves all of the entries in the 
        access request table which have PENDING_APPROVAL status.
        Note that the item format is directly mappable to the dynamodb entry.

        Arguments
        ----------

        Returns
        -------
         : AccessRequestList
            A list of access request entries in the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the items in the registry
    items = get_access_request_entries(user.username, config=config)

    # Filter for pending
    pending_items = list(filter(lambda item: item.status ==
                         RequestStatus.PENDING_APPROVAL, items))

    # package and return
    return AccessRequestList(items=pending_items)


@router.get("/generate-access-report", response_model=AccessReportResponse, operation_id="generate_access_report")
async def generate_access_report(
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> AccessReportResponse:
    """    generate_access_report
        Generates a system access report for the current user token.

        Returns
        -------
         : AccessReportResponse
            The access report object which includes a description of
            access on a per component:role basis.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return AccessReportResponse(
        status=Status(
            success=True,
            details="Generated access report successfully."),
        report=generate_report_from_user(user))
