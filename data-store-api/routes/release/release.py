
from KeycloakFastAPI.Dependencies import ProtectedRole
from ProvenaInterfaces.DataStoreAPI import *
from fastapi import APIRouter, Depends
from config import get_settings, Config
from dependencies.dependencies import read_write_user_protected_role_dependency, email_dependency, admin_user_protected_role_dependency, sys_admin_read_write_user_protected_role_dependency, sys_admin_admin_user_protected_role_dependency, get_user_cipher
from helpers.registry_api_helpers import *
from helpers.release_helpers import add_reviewer, delete_reviewer_by_id, get_all_reviewers, perform_action_of_approval_request, perform_approval_request
from helpers.auth_helpers import get_user_link
from interfaces.EmailClient import EmailClient

router = APIRouter()


@router.delete("/sys-reviewers/delete", operation_id="delete_reviewer")
async def delete_dataset_reviewer(
    reviewer_id: str,
    protect_roles: ProtectedRole = Depends(
        sys_admin_admin_user_protected_role_dependency), # admin only endpoint
    config: Config = Depends(get_settings),
) -> None:

    delete_reviewer_by_id(reviewer_id, config)


@router.post("/sys-reviewers/add", operation_id="add_reviewer")
async def add_dataset_reviewer(
    reviewer_id: IdentifiedResource,
    protected_roles: ProtectedRole = Depends(
        sys_admin_read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
) -> None:
    
    add_reviewer(reviewer_id, config)


@router.get("/sys-reviewers/list", operation_id="list_reviewers")
async def list_reviewers(
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> Set[IdentifiedResource]:
    """
    List all of the system's dataset reviewers
    """
    # TODO output model.
    return get_all_reviewers(config)


@router.post("/approval-request", operation_id="approval_request")
async def approval_request(
    release_approval_request: ReleaseApprovalRequest,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    email_client: EmailClient = Depends(email_dependency),
    user_cipher: str = Depends(get_user_cipher)
) -> ReleaseApprovalRequestResponse:
    # data store URL prefix for handles
    def datastore_url_resolver(id: str) -> str:
        return f"https://data.{config.domain_base}/dataset/{id}?view=approvals"

    # The user must be associated with a linked Person
    linked_person = get_user_link(
        user=protected_roles.user,
        config=config
    )

    if linked_person is None:
        raise HTTPException(
            status_code=400,
            detail=f"You cannot request a review without having a linked Person in the registry."
        )

    await perform_approval_request(
        user_cipher=user_cipher,
        release_approval_request=release_approval_request,
        email_client=email_client,
        datastore_url_resolver=datastore_url_resolver,
        requester_id=linked_person,
        config=config,
        protected_roles=protected_roles
    )

    # here without a http exception, success.
    return ReleaseApprovalRequestResponse(
        dataset_id=release_approval_request.dataset_id,
        approver_id=release_approval_request.approver_id,
        details="Successfully sent request to approve dataset release to approver. Email notification included."
    )


@router.put("/action-approval-request", operation_id="action_approval_request")
async def action_approval_request(
    action_approval_request: ActionApprovalRequest,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    email_client: EmailClient = Depends(email_dependency),
    user_cipher: str = Depends(get_user_cipher)
) -> ActionApprovalRequestResponse:
    # data store URL prefix for handles
    def datastore_url_resolver(id: str) -> str:
        return f"https://data.{config.domain_base}/dataset/{id}?view=approvals"
    await perform_action_of_approval_request(
        user_cipher=user_cipher,
        config=config,
        email_client=email_client,
        datastore_url_resolver=datastore_url_resolver,
        protected_roles=protected_roles,
        action_approval_request=action_approval_request,
    )

    # here without http exception, success.
    return ActionApprovalRequestResponse(
        dataset_id=action_approval_request.dataset_id,
        approved=action_approval_request.approve,
        details="Succesfully responded to dataset release approval request."
    )
