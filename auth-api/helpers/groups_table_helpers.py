import json
from fastapi import HTTPException
from KeycloakFastAPI.Dependencies import *
from config import Config
from SharedInterfaces.AuthAPI import *
import boto3  # type: ignore
from helpers.groups_helpers import *

# Pull out the properties of the metadata model
METADATA_PROPERTIES = list(UserGroupMetadata.__fields__.keys())
METADATA_EXPRESSION = ", ".join(METADATA_PROPERTIES)


def get_group_metadata(
    id: str,
    config: Config
) -> Optional[UserGroupMetadata]:
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.user_groups_table_name)

    # Get item
    try:
        response = table.get_item(
            Key={
                'id': id
            },
            ProjectionExpression=METADATA_EXPRESSION
        )
    except Exception as e:
        # something went wrong when retrieving
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access user group table. Error: {e}')
        )

    # does the item exist?
    if "Item" in response.keys():
        try:
            return UserGroupMetadata.parse_obj(response['Item'])
        except Exception as e:
            # Parse failure - probably happens if there are entries with old invalid format
            raise HTTPException(
                status_code=500,
                detail=f"Error encountered when parsing objects from user group table: {e}"
            )
    else:
        return None


def get_populated_group(
    id: str,
    config: Config
) -> Optional[UserGroup]:
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.user_groups_table_name)

    # Get item
    try:
        response = table.get_item(
            Key={
                'id': id
            }
        )
    except Exception as e:
        # something went wrong when retrieving
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access user group table. Error: {e}')
        )

    # does the item exist?
    if "Item" in response.keys():
        try:
            return UserGroup.parse_obj(response['Item'])
        except Exception as e:
            # Parse failure - probably happens if there are entries with old invalid format
            raise HTTPException(
                status_code=500,
                detail=f"Error encountered when parsing objects from user group table: {e}"
            )
    else:
        return None


def list_group_metadata(
    config: Config
) -> List[UserGroupMetadata]:
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.user_groups_table_name)

    try:
        items = []

        # Start scan
        response = table.scan(
            # only get metadata fields
            ProjectionExpression=METADATA_EXPRESSION
        )

        # Add elements
        items.extend(
            list(map(lambda ele: UserGroupMetadata.parse_obj(ele), response['Items'])))

        # is not empty. (i.e., haven't finished scanning all the table.)
        while 'LastEvaluatedKey' in response.keys():
            # Scan again
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
                # only get metadata fields
                ProjectionExpression=METADATA_EXPRESSION
            )
            # Extend list
            items.extend(
                list(map(lambda ele: UserGroupMetadata.parse_obj(ele), response['Items'])))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to scan the Database. Error: {e}")
        )

    return items


def list_full_groups(
    config: Config
) -> List[UserGroup]:
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.user_groups_table_name)

    try:
        items = []

        # Start scan
        response = table.scan(
        )

        # Add elements
        items.extend(
            list(map(lambda ele: UserGroup.parse_obj(ele), response['Items'])))

        # is not empty. (i.e., haven't finished scanning all the table.)
        while 'LastEvaluatedKey' in response.keys():
            # Scan again
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
            )
            # Extend list
            items.extend(
                list(map(lambda ele: UserGroup.parse_obj(ele), response['Items'])))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to scan the Database. Error: {e}")
        )

    return items


def list_all_items(
    table: Any,
) -> List[Dict[str, Any]]:
    try:
        # compile response items
        items: List[Dict[str, Any]] = []
        response = table.scan()

        # iterate through items and append - don't bother parsing yet
        for item in response["Items"]:
            items.append(item)

        # is not empty. (i.e., haven't finished scanning all the table.)
        while 'LastEvaluatedKey' in response.keys():
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
            )
            for item in response["Items"]:
                items.append(item)

    # Catch any errors
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to scan the Database. Error: {e}")
        )
    # Return the list of items that was retrieved
    return items


def safe_group_write(
    group: UserGroup,
    config: Config
) -> None:
    safe_dict = json.loads(group.json(exclude_none=True))
    raw_write(payload=safe_dict, config=config)


def write_new_group(
    metadata: UserGroupMetadata,
    config: Config
) -> None:
    # check there is no existing group
    try:
        group = get_group_metadata(id=metadata.id, config=config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check for existing group with ID: {metadata.id}. Aborting. Error: {e}."
        )

    if group is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Tried to write a new group (id={metadata.id}) but there is an existing group! Update instead or remove first."
        )

    # all good to go
    full_group = UserGroup(
        id=metadata.id,
        display_name=metadata.display_name,
        description=metadata.description,
        default_data_store_access=metadata.default_data_store_access,
        users=[]
    )
    safe_group_write(group=full_group, config=config)


def add_group_user(
    id: str,
    user: GroupUser,
    config: Config
) -> None:
    # Get existing group
    group = get_populated_group(id=id, config=config)

    if group is None:
        raise HTTPException(
            status_code=400,
            detail=f"Tried to add a user to group {id} but no such group was found."
        )

    # add the user
    username = user.username
    if username in produce_username_set(group):
        raise HTTPException(
            status_code=400,
            detail=f"Tried to add a user to group {id} but the user was already a member of the group."
        )

    group.users.append(user)

    # update the entry
    safe_group_write(group=group, config=config)


def remove_group_user(
    id: str,
    user: GroupUser,
    config: Config
) -> None:
    # Get existing group
    group = get_populated_group(id=id, config=config)

    if group is None:
        raise HTTPException(
            status_code=400,
            detail=f"Tried to remove a user from group {id} but no such group was found."
        )

    # remove the user
    if user.username not in produce_username_set(group):
        raise HTTPException(
            status_code=400,
            detail=f"Tried to remove specified user from group with id {id} but the user was not found in the group."
        )

    # filter the groups user list to remove matching username
    group.users = list(filter(lambda u: u.username != user.username, group.users))

    # update the entry
    safe_group_write(group=group, config=config)


def remove_group_users(
    id: str,
    users: List[GroupUser],
    config: Config
) -> None:
    # Get existing group
    group = get_populated_group(id=id, config=config)

    # Check the group exists
    if group is None:
        raise HTTPException(
            status_code=400,
            detail=f"Tried to remove a user from group {id} but no such group was found."
        )

    # check all members exist
    existing_usernames = produce_username_set(group)
    removing_usernames: Set[str] = set()
    for user in users:
        username = user.username
        if username not in existing_usernames:
            raise HTTPException(
                status_code=400,
                detail=f"Tried to remove specified user with username {username} from group with id {id} but the user was not found in the group. No users removed!"
            )
        removing_usernames.add(username)

    # filter the groups user list to remove matching username
    group.users = list(
        filter(lambda u: u.username not in removing_usernames, group.users))

    # update the entry
    safe_group_write(group=group, config=config)


def delete_group(
    id: str,
    config: Config
) -> None:
    # check the group exists
    group = get_group_metadata(id=id, config=config)
    if not group:
        raise HTTPException(
            status_code=400, detail=f"Tried to delete group with ID: {id} but it does not exist!"
        )

    # delete it now
    delete_entry(id=id, config=config)


def update_group_metadata(
    group: UserGroupMetadata,
    config: Config
) -> None:
    # make sure group exists and get all data
    existing_group = get_populated_group(id=group.id, config=config)
    if not existing_group:
        raise HTTPException(
            status_code=400, detail=f"Tried to update group with ID: {group.id} but it does not exist!"
        )
    # add groups field to metadata
    full_group = UserGroup(
        id=group.id,
        display_name=group.display_name,
        description=group.description,
        users=existing_group.users,
        default_data_store_access=group.default_data_store_access
    )
    # write the updated group
    safe_group_write(
        group=full_group,
        config=config
    )


def write_dynamo_db_entry_raw(item: Dict[str, Any], table: Any) -> None:
    """    write_dynamo_db_entry_raw
        Given the unparsed entry and the dynamo db table will write 
        the entry to the table. 

        Arguments
        ----------
        item : Dict[str, Any]
            The item to write - this method is unprotected in that a validation 
            failure may occur if the item is not dynamoDB compatible
        table : Any
            The boto3 dynamodb table resource

        Raises
        ------
        Exception
            Something goes wrong during writing

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # serialise to remove unsupported datetime objects and similar
    try:
        table.put_item(Item=item)
    except Exception as e:
        raise Exception(f"Failed to write raw entry to table. Error: {e}")


def raw_write(
    payload: Dict[str, Any],
    config: Config
) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(config.user_groups_table_name)

    # write Item to table
    try:
        table.put_item(Item=payload)
    except Exception as e:
        raise Exception(f"Failed to write to table. Error: {e}")


def delete_entry_with_table(
    id: str,
    table: Any
) -> None:
    # Delete item
    try:
        table.delete_item(
            Key={
                'id': id
            }
        )
    except Exception as e:
        # something went wrong when deleting
        raise HTTPException(
            status_code=500,
            detail=(
                f'Failed to delete item from user groups table. Error: {e}')
        )


def delete_entry(
    id: str,
    config: Config
) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(config.user_groups_table_name)
    delete_entry_with_table(id=id, table=table)


def get_table_from_name(table_name: str) -> Any:
    """    get_table_from_name
        Generates a dynamodb resource table to be 
        used in the below methods. 

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(table_name)
    return table


def get_groups_table(config: Config) -> Any:
    """    get_groups_table
        Returns a boto dynamodb table for the groups table

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return get_table_from_name(table_name=config.user_groups_table_name)
