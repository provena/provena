from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from SharedInterfaces.AuthAPI import *
from helpers.groups_helpers import *
from helpers.groups_table_helpers import *
from config import Config, get_settings

router = APIRouter(
    prefix="/user"
)


@router.get("/list_groups", response_model=ListGroupsResponse, operation_id="user_list_groups")
async def list_groups(
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> ListGroupsResponse:
    """
    list_groups 

    Lists the groups and retrieves the metadata for each.

    Returns
    -------
    ListGroupsResponse
        The list of groups
    """
    # fetch the groups
    groups = list_group_metadata(config=config)

    return ListGroupsResponse(
        status=Status(
            success=True, details=f"Retrieved {len(groups)} groups successfully"),
        groups=groups
    )


@router.get("/describe_group", response_model=DescribeGroupResponse, operation_id="user_describe_group")
async def describe_group(
    id: str,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> DescribeGroupResponse:
    """
    describe_group 

    Describes a given group by providing its metadata.

    Parameters
    ----------
    id : str
        The ID of the group

    Returns
    -------
    DescribeGroupResponse
        The group metadata and status
    """
    # fetch the group - None if not found
    group = get_group_metadata(id=id, config=config)

    if group:
        return DescribeGroupResponse(
            status=Status(success=True, details=f"Group metadata retrieved."),
            group=group
        )
    else:
        return DescribeGroupResponse(
            status=Status(
                success=False, details=f"No group with id {id} was found.")
        )


@router.get("/list_user_membership", response_model=ListUserMembershipResponse, operation_id="user_list_user_groups")
async def list_user_membership(
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> ListUserMembershipResponse:
    """
    list_user_membership 

    For a given user identified by username, gets the metadata of the groups they
    are in.

    Returns
    -------
    ListUserMembershipResponse
        The list of group metadata for that users groups
    """
    username = user.username
    # TODO optimise this to avoid scans
    full_groups = list_full_groups(config=config)
    groups: List[UserGroupMetadata] = []
    for group in full_groups:
        found = False
        for group_user in group.users:
            if group_user.username == username:
                found = True
                break
        if found:
            # unpack the user group into just metadata
            groups.append(UserGroupMetadata(**group.dict()))
    return ListUserMembershipResponse(
        status=Status(
            success=True, details=f"Member is part of {len(groups)} groups as listed."),
        groups=groups
    )


@router.get("/list_members", response_model=ListMembersResponse, operation_id="user_list_members")
async def list_members(
    id: str,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> ListMembersResponse:
    """
    list_members 
    Lists the members of a group identified by ID.

    Parameters
    ----------
    id : str
        The group ID

    Returns
    -------
    ListMembersResponse
        The list of users
    """
    # check if part of group
    membership_response = membership_check(
        group_id=id,
        config=config,
        username=user.username
    )

    if not membership_response.status.success:
        return ListMembersResponse(
            status=membership_response.status
        )

    if membership_response.is_member is None:
        raise HTTPException(
            status_code=500,
            detail=f"Membership check was successful but didn't report membership. Contact admin."
        )
    
    # membership check was successful, are they a member?
    if membership_response.is_member:
        full_group = get_populated_group(id=id, config=config)
        if full_group:
            return ListMembersResponse(
                status=Status(
                    success=True, details=f"Group with {len(full_group.users)} returned."),
                group=full_group
            )
        else:
            return ListMembersResponse(
                status=Status(
                    success=False, details=f"No group with id {id} was found.")
            )
    else:
        return ListMembersResponse(
            status=Status(
                success=False, details=f"You are not a member of group with id {id}.")
        )
        


def membership_check(
    group_id: str,
    config: Config,
    username: str,
) -> CheckMembershipResponse:
    full_group = get_populated_group(id=group_id, config=config)
    if not full_group:
        return CheckMembershipResponse(
            status=Status(
                success=False, details=f"No group with id {group_id} was found.")
        )
    member: bool = username in produce_username_set(group=full_group)
    return CheckMembershipResponse(
        status=Status(
            success=True, details=f"Group was found and membership determined."),
        is_member=member
    )


@router.get("/check_membership", response_model=CheckMembershipResponse, operation_id="user_check_membership")
async def check_membership(
    group_id: str,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> CheckMembershipResponse:
    """
    check_membership 

    Checks if the given user (identified by username) is part of the specified
    group (identified by ID).

    Parameters
    ----------
    group_id : str
        The ID of the group to check membership for

    Returns
    -------
    CheckMembershipResponse
        Status and is_member boolean response
    """
    return membership_check(
        group_id=group_id,
        config=config,
        username=user.username
    )
