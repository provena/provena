from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from ProvenaInterfaces.AuthAPI import *
from helpers.groups_table_helpers import *
from helpers.groups_helpers import *
from config import Config, get_settings

router = APIRouter(
    prefix="/admin"
)


@router.get("/list_groups", response_model=ListGroupsResponse, operation_id="admin_list_groups")
async def list_groups(
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
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


@router.get("/describe_group", response_model=DescribeGroupResponse, operation_id="admin_describe_group")
async def describe_group(
    id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
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


@router.get("/list_members", response_model=ListMembersResponse, operation_id="admin_list_members")
async def list_members(
    id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
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
    full_group = get_populated_group(id=id, config=config)
    if full_group:
        return ListMembersResponse(
            status=Status(
                success=True, details=f"Group with {len(full_group.users)} users returned."),
            group=full_group
        )
    else:
        return ListMembersResponse(
            status=Status(
                success=False, details=f"No group with id {id} was found.")
        )


@router.get("/list_user_membership", response_model=ListUserMembershipResponse, operation_id="admin_list_user_groups")
async def list_user_membership(
    username: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> ListUserMembershipResponse:
    """
    list_user_membership 

    For a given user identified by username, gets the metadata of the groups they
    are in.

    Parameters
    ----------
    username : GroupUser
        The users username

    Returns
    -------
    ListUserMembershipResponse
        The list of group metadata for that users groups
    """
    # TODO optimise this to avoid scans
    full_groups = list_full_groups(config=config)
    groups: List[UserGroupMetadata] = []
    for group in full_groups:
        found = False
        for user in group.users:
            if user.username == username:
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


@router.get("/check_membership", response_model=CheckMembershipResponse, operation_id="admin_check_membership")
async def check_membership(
    group_id: str,
    username: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_read_dependency)
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


@router.post("/add_member", response_model=AddMemberResponse, operation_id="admin_add_member")
async def add_member(
    user: GroupUser,
    group_id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> AddMemberResponse:
    """
    add_member 

    Adds the given fully described user to the specified group.

    Parameters
    ----------
    user : GroupUser
        The user to add
    group_id : str
        The group ID

    Returns
    -------
    AddMemberResponse
        Success response
    """
    add_group_user(
        id=group_id,
        user=user,
        config=config
    )
    return AddMemberResponse(
        status=Status(
            success=True, details=f"User added to group {group_id} successfully.")
    )


@router.delete("/remove_member", response_model=RemoveMemberResponse, operation_id="admin_remove_member")
async def remove_member(
    username: str,
    group_id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> RemoveMemberResponse:
    """
    remove_member 

    Removes the given member from the specified user group.

    Parameters
    ----------
    username : str
        The users username to be removed
    group_id : str
        The ID of the group

    Returns
    -------
    RemoveMemberResponse
        Success or failure response
    """
    print(f"Removing user {username}.")
    remove_group_user(
        id=group_id,
        user=GroupUser(username=username),
        config=config
    )
    return RemoveMemberResponse(
        status=Status(
            success=True, details=f"User {username} removed from group {group_id} successfully.")
    )


@router.delete("/remove_members", response_model=RemoveMemberResponse, operation_id="admin_remove_members")
async def remove_members(
    remove_request: RemoveMembersRequest,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> RemoveMemberResponse:
    """
    remove_member 

    Removes a list of members from a specified group. Fails if any of the
    members don't exist and won't write changes unless all members succeed.

    Parameters
    ----------
    remove_request: RemoveMembersRequest
        contains the group ID and list of user usernames to remove

    Returns
    -------
    RemoveMemberResponse
        Success or failure response
    """
    print(
        f"Removing {len(remove_request.member_usernames)} users from group {remove_request.group_id}.")
    remove_group_users(
        id=remove_request.group_id,
        users=list(map(lambda username: GroupUser(
            username=username), remove_request.member_usernames)),
        config=config
    )
    return RemoveMemberResponse(
        status=Status(
            success=True,
            details=f"{len(remove_request.member_usernames)} users were removed from group {remove_request.group_id} successfully.")
    )


@router.post("/add_group", response_model=AddGroupResponse, operation_id="admin_add_group")
async def add_group(
    metadata: UserGroupMetadata,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> AddGroupResponse:
    """
    add_group 

    Creates a new group. Will fail if group already exists.

    Parameters
    ----------
    metadata : UserGroupMetadata
        The metadata for the group, including a unique ID.

    Returns
    -------
    AddGroupResponse
        Success or failure response
    """
    write_new_group(
        metadata=metadata,
        config=config
    )
    return AddGroupResponse(
        status=Status(
            success=True, details=f"Successfully created group with id: {metadata.id}.")
    )


@router.delete("/remove_group", response_model=RemoveGroupResponse, operation_id="admin_remove_group")
async def remove_group(
    id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_admin_dependency)
) -> RemoveGroupResponse:
    """
    remove_group 

    Removes a group - will fail if the group doesn't already exist.

    Parameters
    ----------
    id : str
        The ID of the group to delete.

    Returns
    -------
    RemoveGroupResponse
        Success of failure response.
    """
    delete_group(
        id=id,
        config=config
    )
    return RemoveGroupResponse(
        status=Status(
            success=True, details=f"Successfully removed group with id: {id}.")
    )


@router.put("/update_group", response_model=UpdateGroupResponse, operation_id="admin_update_group")
async def update_group(
    metadata: UserGroupMetadata,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> UpdateGroupResponse:
    """
    update_group 

    Updates the given groups metadata. The metadata includes the ID of the group
    to be updated.

    Parameters
    ----------
    metadata : UserGroupMetadata
        The updated metadata including ID

    Returns
    -------
    UpdateGroupResponse
        Success or failure response
    """
    update_group_metadata(
        group=metadata,
        config=config
    )
    return UpdateGroupResponse(
        status=Status(
            success=True, details=f"Successfully updated metadata for group with id: {metadata.id}.")
    )
