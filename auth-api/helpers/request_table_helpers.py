import json
from fastapi import HTTPException
from KeycloakFastAPI.Dependencies import *
from config import Config
from SharedInterfaces.AuthAPI import *
import boto3  # type: ignore
from boto3.dynamodb.conditions import Key  # type: ignore
from typing import Optional, Tuple
from datetime import datetime, timedelta


def generate_status_change_email_text(
    username: str,
    original_status: RequestStatus,
    new_status: RequestStatus,
    request_entry: RequestAccessTableItem
) -> str:
    """    generate_status_change_email_text
        Generates the body for the status change email sent to users

        Arguments
        ----------
        username: str
            The username of recipient
        original_status: RequestStatus
            The original status of the role request
        new_status: RequestStatus
            The new status of the role request
        request_entry: RequestAccessTableItem
            The request entry for the table

        Returns
        -------
         : str
            The body of the email.


        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    original_friendly_format = REQUEST_STATUS_TO_USER_EXPLANATION[original_status]
    new_friendly_format = REQUEST_STATUS_TO_USER_EXPLANATION[new_status]
    header = f"Subject: Status update for Provena access request {request_entry.request_id}"
    body = \
        f"""Request for access change for username: {username} request_id: {request_entry.request_id}.
        
Your request has changed from '{original_friendly_format}' to '{new_friendly_format}'.

You requested: 
    """

    diff_report = AccessReport.parse_obj(
        json.loads(request_entry.request_diff_contents))
    component_list = []
    for component in diff_report.components:
        component_string_rows = []
        for role in component.component_roles:
            component_string_rows.append(
                f"Role name: {role.role_name}, desired access: {'Granted' if role.access_granted else 'Denied'}")
        component_list.append(
            f"Component: {component.component_name}\n" + '\n'.join(component_string_rows))
    component_body = '\n'.join(component_list)

    notes = "Your request has the following notes:\n" + \
        '\n'.join(request_entry.notes.split(','))

    return header + "\n\n" + body + "\n" + component_body + "\n\n" + notes


def write_access_request_entry(
    item: RequestAccessTableItem,
    config: Config
) -> None:
    """    write_access_request_entry
        Given a request access table item will write this entry to 
        the dynamodb table specified by the environment variable table
        name.

        Arguments
        ----------
        item : RequestAccessTableItem
            The dynamodb item represented as pydantic model.

        Raises
        ------
        Exception
            Due to error writing to table.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(config.access_request_table_name)

    # Get dictionary representation of the item
    write_item = item.dict()

    # write Item to table
    try:
        table.put_item(Item=write_item)
    except Exception as e:
        raise Exception(f"Failed to write to table. Error: {e}")

    return


def create_new_request_entry(
    user: User,
    diff_report: AccessReport,
    complete_report: AccessReport,
    config: Config,
    notes: List[str] = [],
) -> RequestAccessTableItem:
    """    create_new_request_entry
        Will generate a new entry for the request access table 
        which has the PENDING_APPROVAL state pulling the user 
        info from the user object. Also includes the diff report
        and the complete report to record this info at time of 
        record creation

        Arguments
        ----------
        user : User
            The user to create record for. 
        diff_report : AccessReport
            The access report diff which was requested.
        complete_report : AccessReport
            Current access from token.
        notes : List[str], optional. 
            list of notes to add. Defaults to empty list, [].

        Returns
        -------
         : RequestAccessTableItem
            The dynamodb item in pydantic model form ready to write

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    notes_serialised = ','.join(notes)

    # Serialized access report
    diff_report_serialized = diff_report.json()
    complete_report_serialized = complete_report.json()

    # Work out the expiry delta
    expiry_delta = timedelta(days=config.request_expiry_days)

    # Create and return record for table
    return RequestAccessTableItem(
        username=user.username,
        # email is usually included but in other case
        # use the username as email address
        email=user.email if user.email else user.username,
        # TODO better request ID just using timestamp for now
        request_id=int(datetime.now().timestamp()),
        expiry=int((datetime.now() + expiry_delta).timestamp()),
        created_timestamp=int(datetime.now().timestamp()),
        updated_timestamp=int(datetime.now().timestamp()),
        status=RequestStatus.PENDING_APPROVAL,
        ui_friendly_status=REQUEST_STATUS_TO_USER_EXPLANATION[RequestStatus.PENDING_APPROVAL],
        notes=notes_serialised,
        request_diff_contents=diff_report_serialized,
        complete_contents=complete_report_serialized
    )


def delete_request_entry(
    username: str,
    request_id: int,
    config: Config
) -> None:
    """    delete_request_entry
        Given the username/request id will delete the entry. 
        Use with caution, we may not need to remove entries as 
        they are useful for auditing. But this is provided as need
        be for sys admin users.

        Will succeed if no entry exists.

        Arguments
        ----------
        username : str
            Username
        request_id : int
            Request id

        Raises
        ------
        HTTPException
            If something goes wrong with delete op.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.access_request_table_name)

    # Get item
    try:
        table.delete_item(
            Key={
                'username': username,
                'request_id': request_id
            }
        )
    except Exception as e:
        # something went wrong when deleting
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access request table. Error: {e}')
        )


def get_request_entry(
    username: str,
    request_id: int,
    config: Config
) -> Optional[RequestAccessTableItem]:
    """    get_request_entry
        Given a username and request id will make a request against
        the request access table and retrieve the corresponding record.

        Returns None if the object is not present.

        Arguments
        ----------
        username : str
            username to retrieve 
        request_id : int
            Request unique id (which is sort key against username)

        Returns
        -------
         : Optional[RequestAccessTableItem]
            Returns the entry if present, otherwise None

        Raises
        ------
        HTTPException
            500 error if the table fails to be accessed
        HTTPException
            500 error if parse error from the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.access_request_table_name)

    # Get item
    try:
        response = table.get_item(
            Key={
                'username': username,
                'request_id': request_id
            }
        )
    except Exception as e:
        # something went wrong when retrieving
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access request table. Error: {e}')
        )

    # does the item exist?
    if "Item" in response.keys():
        try:
            return RequestAccessTableItem.parse_obj(response['Item'])
        except Exception as e:
            # Parse failure - probably happens if there are entries with old invalid format
            raise HTTPException(
                status_code=500,
                detail=f"Error encountered when parsing objects from request table: {e}"
            )
    else:
        return None


def get_all_access_request_entries(
    config: Config
) -> List[RequestAccessTableItem]:
    """    get_access_request_entries
        Retrieves ALL entires from the table.

        Arguments
        ----------

        Returns
        -------
         : List[RequestAccessTableItem]
            List of table items

        Raises
        ------
        HTTPException
            Connection/retrieval error
        HTTPException
            Parse error

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.access_request_table_name)

    try:
        items = []

        # Start scan
        response = table.scan()

        # Add elements
        items.extend(
            list(map(lambda ele: RequestAccessTableItem.parse_obj(ele), response['Items'])))

        # is not empty. (i.e., haven't finished scanning all the table.)
        while 'LastEvaluatedKey' in response.keys():
            # Scan again
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'])
            # Extend list
            items.extend(
                list(map(lambda ele: RequestAccessTableItem.parse_obj(ele), response['Items'])))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to scan the Database. Error: {e}")
        )

    return items


def get_access_request_entries(
    username: str,
    config: Config
) -> List[RequestAccessTableItem]:
    """    get_access_request_entries
        For the given username, retrieves all corresponding 
        entries.

        Arguments
        ----------
        username : str
            The username

        Returns
        -------
         : List[RequestAccessTableItem]
            List of table items

        Raises
        ------
        HTTPException
            Connection/retrieval error
        HTTPException
            Parse error

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Get the table
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(config.access_request_table_name)

    # Make query against partition key
    try:
        response = table.query(
            KeyConditionExpression=Key('username').eq(username)
        )
    except Exception as e:
        # Connection error
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access request table. Error: {e}')
        )

    # map into pydantic model
    try:
        return list(map(lambda entry: RequestAccessTableItem.parse_obj(entry), response['Items']))
    except Exception as e:
        # Parse error
        raise HTTPException(
            status_code=500,
            detail=f"Error encountered when parsing objects from request table: {e}"
        )


def check_access_request(
    user: User,
    config: Config
) -> Tuple[bool, str]:
    """    check_access_request
        Given the user will retrieve pending records and 
        decide if the user should be allowed to make another 
        request.

        Arguments
        ----------
        user : User
            The user

        Returns
        -------
         : Tuple(bool,str)
            True/False based on decision, if False includes a message
            explaining why to show on front end

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Get the items in the access request table
    items = get_access_request_entries(user.username, config=config)

    # If no items then all good
    if len(items) == 0:
        return (True, "")

    # If there are items, check the nature of the items

    # Are there pending requests?
    pending_found = False
    newest: Optional[RequestAccessTableItem] = None

    for item in items:
        if item.status == RequestStatus.PENDING_APPROVAL:
            if not newest or item.updated_timestamp > newest.updated_timestamp:
                pending_found = True
                newest = item

    # If pending found check how old
    if pending_found:
        # work out delta
        delta = timedelta(days=config.minimum_request_waiting_time_days)

        # work out max ts
        max_ts = (datetime.now() - delta).timestamp()

        assert newest

        # check if newest is older
        if newest.updated_timestamp < max_ts:
            # This is allowed - they have waited long enough
            return True, ""

        else:
            return False, \
                f"You have a pending request which has been pending less than {config.minimum_request_waiting_time_days} days."

    else:
        # There are no pending requests so enable another request
        return True, ""


def touch_record_timestamp(item: RequestAccessTableItem) -> None:
    """    touch_record_timestamp
        Updates a record with current timestamp

        Arguments
        ----------
        item : RequestAccessTableItem
            The item

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    item.updated_timestamp = int(datetime.now().timestamp())


def append_note_to_item(item: RequestAccessTableItem, note: str) -> None:
    """    append_note_to_item
        Appends a note to an item

        Arguments
        ----------
        item : RequestAccessTableItem
            The item
        note : str
            The note to add

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Some weirdness if empty
    if item.notes == "":
        current_notes = []
    else:
        current_notes = item.notes.split(',')

    # Add note and serialize with comma delimeter
    current_notes.append(note)
    item.notes = ','.join(current_notes)
