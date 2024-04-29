import string
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel
from enum import Enum
# Interface exports prefer relative imports
# where as pip install prefers module level import
try:
    from ProvenaInterfaces.SharedTypes import Status, StatusResponse, ImportMode
    from ProvenaInterfaces.RegistryModels import Roles
except:
    from .SharedTypes import Status, StatusResponse, ImportMode
    from .RegistryModels import Roles

# The groups configuration includes references to the data store specific access
# for a given group
try:
    # from ProvenaInterfaces.DataStoreAPI import GroupActionsConfiguration
    None
except:
    None
    # from .DataStoreAPI import GroupActionsConfiguration


class IntendedUserType(str, Enum):
    """    IntendedUserType
        A list of possible types of users.
    """
    GENERAL = "GENERAL"
    ADMINISTRATOR = "ADMINISTRATOR"


class AccessLevel(str, Enum):
    """    AccessLevel
        Describes the access level of a role e.g. read/write/admin
    """
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class ComponentName(str, Enum):
    HANDLE_SERVICE = "handle-service"
    SYS_ADMIN = "sys-admin"
    ENTITY_REGISTRY = "entity-registry"
    JOB_SERVICE = "job-service"


class ComponentRole(BaseModel):
    """    ComponentRole
        Describes a role which includes all information 
        to understand the name, how to display/describe it 
        and what level it grants
    """
    # The proper keycloak role name
    role_name: str
    # The user friendly display name
    role_display_name: str
    # The level of access this is intended to grant
    # Please handle responsibly on the client side
    role_level: AccessLevel
    # Description of the purpose of the role
    description: str
    # Intended users
    intended_users: List[IntendedUserType]


class AuthorisationComponent(BaseModel):
    """    AuthorisationComponent
        An authorisation component is a component name
        along with a list of roles that component has.
    """
    # A component name, mainly used for displaying
    component_name: ComponentName
    # List of roles that component supports
    component_roles: List[ComponentRole]

    def get_role_at_level(self, desired_level: AccessLevel) -> ComponentRole:
        """    get_role_at_level
            For a given authorisation component, returns the access role which 
            grants the desired level of access. This can be used by dependent 
            components to work out what role name they should be looking for 
            given a particular level of access required.

            Arguments
            ----------
            desired_level : AccessLevel
                The access level this role should provide

            Returns
            -------
             : ComponentRole
                The component role which describes the matching role

            Raises
            ------
            Exception
                If no role is found with a matching level, then an exception is 
                thrown.

            See Also (optional)
            --------

            Examples (optional)
            --------
            read_only_role_name = DATA_STORE_COMPONENT.get_access_at_level(AccessLevel.READ).role_name
        """
        # Search for role with matching level
        for role in self.component_roles:
            if role.role_level == desired_level:
                # Return if found
                return role

        # Can't find the role - throw exception
        raise Exception(
            f'Failed to find a role that provides the correct access level\
              for component {self.component_name}.')


class AuthorisationModel(BaseModel):
    components: List[AuthorisationComponent]

    def get_role_level_for_component(self, component_name: ComponentName, role_level: AccessLevel) -> ComponentRole:
        """    get_role_level_for_component
            Given the component name and role level, will find the component role
            which provides that role level access.

            Arguments
            ----------
            component_name : str
                The component name e.g. data-store
            role_level : AccessLevel
                The desired level of access the role should grant

            Returns
            -------
             : ComponentRole
                The matching component role

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # Search for matching component name
        # then use the get role at level component method
        for comp in self.components:
            if comp.component_name == component_name:
                return comp.get_role_at_level(role_level)

        raise Exception(
            'Unable to find a component with matching component name.')


JOB_COMPONENT = AuthorisationComponent(
    component_name=ComponentName.JOB_SERVICE,
    component_roles=[
        ComponentRole(
            role_name="job-service-admin",
            role_display_name="Job Service Admin",
            role_level=AccessLevel.ADMIN,
            description="Admin role which enables management of jobs including lodging.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="job-service-write",
            role_display_name="Job Service Write",
            role_level=AccessLevel.WRITE,
            description="Allows r/w and lodging of jobs",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="job-service-read",
            role_display_name="Job Service Read",
            role_level=AccessLevel.READ,
            description="Allows reading of all user's jobs",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        )
    ]
)

HANDLE_SERVICE_COMPONENT = AuthorisationComponent(
    component_name=ComponentName.HANDLE_SERVICE,
    component_roles=[
        ComponentRole(
            role_name="handle-read",
            role_display_name="Handle service read only access",
            role_level=AccessLevel.READ,
            description="Allows access to read only functions of the handle service. This enables viewing, retrieving, listing of handles.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="handle-write",
            role_display_name="Handle service write access",
            role_level=AccessLevel.WRITE,
            description="Allows access to read and write functions of the handle service. This enables registering, viewing, retrieving, listing of handles.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="handle-admin",
            role_display_name="Handle service full admin access",
            role_level=AccessLevel.ADMIN,
            description="Allows full access to the handle service.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
    ]
)

SYS_ADMIN_COMPONENT = AuthorisationComponent(
    component_name=ComponentName.SYS_ADMIN,
    component_roles=[
        ComponentRole(
            role_name="sys-admin-read",
            role_display_name="Sys admin read only access",
            role_level=AccessLevel.READ,
            description="Allows read only access to system admin functions. This includes listing and viewing access requests.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="sys-admin-write",
            role_display_name="Sys admin write/read access",
            role_level=AccessLevel.WRITE,
            description="Allows read and write access to system admin functions. This includes listing, viewing, modifying and adding notes to access requests.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="sys-admin-admin",
            role_display_name="Sys admin full access",
            role_level=AccessLevel.ADMIN,
            description="Allows complete access to system admin functions. This includes listing, viewing, modifying, deleting and adding notes to access requests.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
    ]
)

ENTITY_REGISTRY_COMPONENT = AuthorisationComponent(
    component_name=ComponentName.ENTITY_REGISTRY,
    component_roles=[
        ComponentRole(
            role_name="entity-registry-read",
            role_display_name="Entity registry read only access",
            role_level=AccessLevel.READ,
            description="Allows read only access to the entity registry - list, view.",
            intended_users=[
                IntendedUserType.GENERAL,
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="entity-registry-write",
            role_display_name="Entity registry write/read access",
            role_level=AccessLevel.WRITE,
            description="Allows creation and modification of resources in the entity registry.",
            intended_users=[
                IntendedUserType.GENERAL,
                IntendedUserType.ADMINISTRATOR
            ]
        ),
        ComponentRole(
            role_name="entity-registry-admin",
            role_display_name="Entity registry full access",
            role_level=AccessLevel.ADMIN,
            description="Allows all actions against all entity registry resources.",
            intended_users=[
                IntendedUserType.ADMINISTRATOR
            ]
        ),
    ]
)

# Add more components as required here

AUTHORISATION_MODEL = AuthorisationModel(
    components=[
        HANDLE_SERVICE_COMPONENT,
        SYS_ADMIN_COMPONENT,
        ENTITY_REGISTRY_COMPONENT,
        JOB_COMPONENT
        # Add more here as required
    ]
)

# Start of response objects from auth API


class ReportComponentRole(ComponentRole):
    # inherits all component role fields
    # also includes whether this access is granted
    access_granted: bool


class ReportAuthorisationComponent(BaseModel):
    # A component name, mainly used for displaying
    component_name: ComponentName
    # List of roles that component supports
    component_roles: List[ReportComponentRole]


class AccessReport(BaseModel):
    components: List[ReportAuthorisationComponent]


class AccessReportResponse(BaseModel):
    status: Status
    report: AccessReport


class AccessRequestResponse(BaseModel):
    status: Status


class RequestStatus(str, Enum):
    # Initial state
    PENDING_APPROVAL = "PENDING_APPROVAL"

    # Approved and ready to be actioned
    APPROVED_PENDING_ACTION = "APPROVED_PENDING_ACTION"

    # Denied but not deleted - kept for auditing if desired
    DENIED_PENDING_DELETION = "DENIED_PENDING_DELETION"

    # Actioned and not deleted - kept for auditing if desired
    ACTIONED_PENDING_DELETION = "ACTIONED_PENDING_DELETION"


REQUEST_STATUS_TO_USER_EXPLANATION: Dict[RequestStatus, str] = {
    RequestStatus.PENDING_APPROVAL: "request received, awaiting action",
    RequestStatus.APPROVED_PENDING_ACTION: "request approved, action underway",
    RequestStatus.DENIED_PENDING_DELETION: "request denied",
    RequestStatus.ACTIONED_PENDING_DELETION: "request approved and completed",
}


class RequestAccessTableItem(BaseModel):
    # partition key
    username: str
    # sort key
    request_id: int
    # ttl attribute
    expiry: int
    # email address (== username when writing)
    email: str

    # other fields
    created_timestamp: int
    updated_timestamp: int
    status: RequestStatus
    ui_friendly_status: str

    # json serialised string of access report
    # for diff and for complete access report
    request_diff_contents: str
    complete_contents: str

    # comma separated list of notes
    notes: str


class AccessRequestList(BaseModel):
    items: List[RequestAccessTableItem]


class AccessRequestStatusChange(BaseModel):
    username: str
    request_id: int
    desired_state: RequestStatus
    additional_note: Optional[str]


class DeleteAccessRequest(BaseModel):
    username: str
    request_id: int


class RequestAddNote(BaseModel):
    note: str
    username: str
    request_id: int


class ChangeStateStatus(BaseModel):
    state_change: Status
    email_alert: Status


# Group management models

class GroupUser(BaseModel):
    # The username (required)
    username: str
    # the email (optional)
    email: Optional[str]
    # Optional first/last name
    first_name: Optional[str]
    last_name: Optional[str]


class UserGroupMetadata(BaseModel):
    # Unique ID to be used in dynamoDB table
    id: str
    # display name for the group e.g. Coconet Developers
    display_name: str
    # description of the groups purpose/users
    description: str

    # Optional additional metadata

    # Default access configuration for data store datasets - if a member of this
    # group creates a dataset, the dataset will have this group assigned with
    # the following default level. If this isn't provided, then no access will
    # be granted (other than the global default metadata read).
    default_data_store_access: Optional[Roles] = None


class UserGroup(UserGroupMetadata):
    # List of users
    users: List[GroupUser]


class ListGroupsResponse(StatusResponse):
    groups: Optional[List[UserGroupMetadata]]


class DescribeGroupResponse(StatusResponse):
    group: Optional[UserGroupMetadata]


class ListMembersResponse(StatusResponse):
    group: Optional[UserGroup]


class ListUserMembershipResponse(StatusResponse):
    groups: Optional[List[UserGroupMetadata]]


class CheckMembershipResponse(StatusResponse):
    is_member: Optional[bool]


class AddMemberResponse(StatusResponse):
    None


class RemoveMemberResponse(StatusResponse):
    None


class AddGroupResponse(StatusResponse):
    None


class RemoveGroupResponse(StatusResponse):
    None


class UpdateGroupResponse(StatusResponse):
    None


class RemoveMembersRequest(BaseModel):
    group_id: str
    member_usernames: List[str]


# import export revert

class GroupsImportStatistics(BaseModel):
    old_size: int
    new_size: int
    deleted_entries: int
    overwritten_entries: int
    new_entries: int


class GroupsExportResponse(StatusResponse):
    items: Optional[List[Dict[str, Any]]]


class GroupsImportSettings(BaseModel):
    import_mode: ImportMode

    # Should the items supplied be parsed before being
    # added/overwritten
    parse_items: bool = True

    # Always force explicit deletion flag even if mode enables it
    allow_entry_deletion: bool = False

    # Should the changes be written - true means no writing false means write
    # the changes
    trial_mode: bool = True


class GroupsRestoreRequest(GroupsImportSettings):
    None


class GroupsImportRequest(GroupsImportSettings):
    items: List[Dict[str, Any]]


class GroupsImportResponse(StatusResponse):
    trial_mode: bool
    statistics: Optional[GroupsImportStatistics]
    failure_list: Optional[List[Tuple[str, Dict[str, Any]]]]


class UsernamePersonLinkTableEntry(BaseModel):
    # both fields required

    # primary
    username: str
    # Standard-none, GSI-primary
    person_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1

# User -> Lookup
# Request = qstring no JSON body


class UserLinkUserLookupResponse(BaseModel):
    # Response

    # only included if present
    person_id: Optional[str]
    # included to specify if the link existed
    success: bool

# User -> Assign


class UserLinkUserAssignRequest(BaseModel):
    # username is implicit in token
    person_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1


class UserLinkUserValidateRequest(BaseModel):
    # username is implicit in token
    person_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1


class UserLinkUserValidateResponse(StatusResponse):
    # Just returns 200 OK but includes status for any issues
    pass


class UserLinkUserAssignResponse(BaseModel):
    # Just returns 200 OK, else 400/500 error with details
    pass

# Admin -> Lookup
# Request = qstring no JSON body


class AdminLinkUserLookupResponse(BaseModel):
    # Response

    # only included if present
    person_id: Optional[str]
    # included to specify if the link existed
    success: bool

# Admin -> Assign


class AdminLinkUserAssignRequest(BaseModel):
    # supply username
    username: str
    # username is implicit in token
    person_id: str
    # validate existence of item?
    validate_item: bool = True
    # force if existing
    force: bool = False

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1


class AdminLinkUserAssignResponse(BaseModel):
    # Just returns 200 OK, else 400/500 error with details
    pass


class AdminLinkUserClearResponse(BaseModel):
    # Just returns 200 OK, else 400/500 error with details
    pass


class UserLinkReverseLookupResponse(BaseModel):
    # the list of usernames that associate with that person_id, if any
    usernames: List[str]
