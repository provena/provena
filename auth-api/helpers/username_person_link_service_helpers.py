import json
from fastapi import HTTPException
from config import Config
import boto3  # type: ignore
from typing import Optional
from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.RegistryAPI import AccessSettings
from helpers.util import py_to_dict
from boto3.dynamodb.conditions import Key  # type: ignore


def id_appears_valid(id: str) -> bool:
    """

    Ensures that an id possibly returned as a link lookup appears to be valid. 

    TODO destub if becomes issue - currently checks non empty.

    Args:
        id (string): The id result

    Returns:
        bool: Is it valid looking?
    """
    return id != ""


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


def get_username_person_link_table(config: Config) -> Any:
    """  
        Returns a boto dynamodb table for the username person link table

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return get_table_from_name(table_name=config.username_person_link_table_name)


def get_link_entry_by_username(
    username: str,
    config: Config
) -> Optional[UsernamePersonLinkTableEntry]:
    """
    Looks up the specified username from the username person link service table.

    Args:
        username (str): The username
        config (Config): app config

    Returns:
        Optional[UsernamePersonLinkTableEntry]: If present, the parsed table entry.
    """
    # Get the table
    table = get_username_person_link_table(config=config)

    # Get item
    try:
        response = table.get_item(
            Key={
                'username': username
            },
        )
    except Exception as e:
        # something went wrong when retrieving
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access user link service table. Error: {e}')
        )

    # does the item exist?
    if "Item" in response.keys():
        try:
            return UsernamePersonLinkTableEntry.parse_obj(response['Item'])
        except Exception as e:
            # Parse failure - probably happens if there are entries with old invalid format
            raise HTTPException(
                status_code=500,
                detail=f"Error encountered when parsing object from user link service table: {e}"
            )
    else:
        return None


def set_link_entry_by_username(
    entry: UsernamePersonLinkTableEntry,
    config: Config
) -> None:
    # Get the table
    table = get_username_person_link_table(config=config)

    # parse the payload into good safe format
    payload = py_to_dict(entry)

    # Set item
    try:
        table.put_item(Item=payload)
    except Exception as e:
        # something went wrong when writing
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to write to user link service table. Error: {e}')
        )


def check_is_owner(username: str, settings: AccessSettings) -> bool:
    """
    Returns true iff the user is the owner based on comparing usernames.

    Args:
        username (str): The username of the user to test
        settings (AccessSettings): The auth configuration of the registry item

    Returns:
        bool: True iff owner
    """
    return settings.owner == username


def del_link_entry_by_username(
    username: str,
    config: Config
) -> None:
    """

    Deletes the link service entry by username.

    Admin only.

    Args:
        username (str): The username to clear (primary key)
        config (Config): App config
    """
    # Get the table
    table = get_username_person_link_table(config=config)

    # Set item
    try:
        table.delete_item(
            Key={
                'username': username
            }
        )
    except Exception as e:
        # something went wrong when writing
        raise HTTPException(
            status_code=500,
            detail=(
                f'Failed to delete from user link service table. Error: {e}')
        )


def get_link_entries_by_person_id(
    person_id: str,
    config: Config
) -> List[UsernamePersonLinkTableEntry]:
    """
    Looks up the specified person_id from the link service table.

    Uses the GSI to do a reverse lookup with scanning

    Args:
        person_id (str): The person_id
        config (Config): app config

    Returns:
        Optional[UsernamePersonLinkTableEntry]: If present, the parsed table entry.
    """
    # Get the table
    table = get_username_person_link_table(config=config)

    # secondary index name
    gsi_name = config.username_person_link_table_person_index_name

    qparams = {
        'IndexName':  gsi_name,
        'KeyConditionExpression': Key('person_id').eq(person_id)
    }

    # Get item(s)
    try:
        response = table.query(
            **qparams
        )
    except Exception as e:
        # something went wrong when retrieving
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access user link service table. Error: {e}')
        )

    def parse_item(item: Dict[str, Any]) -> UsernamePersonLinkTableEntry:
        try:
            return UsernamePersonLinkTableEntry.parse_obj(item)
        except Exception as e:
            # Parse failure - probably happens if there are entries with old invalid format
            raise HTTPException(
                status_code=500,
                detail=f"Error encountered when parsing object from user link service table: {e}"
            )

    # return the parsed list of results - probably one but could be multiple!
    return list(map(parse_item, response['Items']))
