from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
from fastapi import HTTPException
from KeycloakFastAPI.Dependencies import User
from helpers.dynamo_helpers import get_lock_entry, write_lock_table_entry
from config import Config


def get_item_from_lock_table(id: str, config: Config) -> LockTableEntry:
    # get the entry
    try:
        entry_raw = get_lock_entry(id=id, config=config)
    except KeyError as ke:
        raise ke
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while accessing the lock database, error: {e}."
        )

    # parse the entry
    try:
        parsed = LockTableEntry.parse_obj(entry_raw)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"The lock entry was not a valid Lock object, parse failure. Error: {e}."
        )

    return parsed


def generate_default_lock_information() -> LockInformation:
    """
    generate_default_lock_information 

    Generates a default empty unlocked config

    Returns
    -------
    LockInformation
        The lock config
    """
    return LockInformation(
        locked=False,
        history=[]
    )


def check_if_locked(lock_information: LockInformation) -> bool:
    """
    check_if_locked 

    Interrogates a resource to determine if it is locked

    Parameters
    ----------
    lock_information : LockInformation
        The registry lock information

    Returns
    -------
    bool
        True iff resource is currently locked
    """
    return lock_information.locked


def get_lock_status(id: str, config: Config) -> bool:
    """
    get_lock_status 

    Fetches the lock information for an item from the lock table and returns
    boolean.


    Parameters
    ----------
    id : str
        The resource ID

    Returns
    -------
    bool
        True = locked. False = unlocked.
    """
    # fetch the lock metadata based on id
    try:
        lock_item: LockTableEntry = get_item_from_lock_table(
            id=id,
            config=config
        )
    except KeyError as e:  # handle not in table.
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve ID {id} from the lock table, are you sure it exists?"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(
            f"Something unexpected went wrong during resource data retrieval. Error: {e}")

    return check_if_locked(
        lock_information=lock_item.lock_information
    )


def apply_lock(lock_information: LockInformation, reason: str, user: User) -> LockInformation:
    """
    apply_lock 

    Lock the resource - applies updates to the record lock configuration.

    In place mutation of lock information - just returns same reference.

    Parameters
    ----------
    lock_information: LockInformation
        The current lock status
    reason : str
        The reason provided by the user for the lock change
    user : User
        The user

    Returns
    -------
    LockInformation
        Updated lock information

    Raises
    ------
    HTTPException
        If the resource is already locked = 400
    """

    # If the resource is already locked then raise an error
    if lock_information.locked:
        raise HTTPException(
            status_code=400,
            detail=f"Resource is already locked."
        )

    # Apply the change to the resource

    # Lock it
    lock_information.locked = True
    # Add history
    lock_information.history.append(
        LockEvent(
            action_type=LockActionType.LOCK,
            username=user.username,
            email=user.email,
            reason=reason,
            timestamp=int(datetime.now().timestamp())
        )
    )

    # return updated resource
    return lock_information


def apply_unlock(lock_information: LockInformation, reason: str, user: User) -> LockInformation:
    """
    apply_unlock 

    Unlock the resource - applies updates to the record lock configuration.

    In place mutation of lock information - just returns same reference.

    Parameters
    ----------
    lock_information: LockInformation
        The current lock status
    reason : str
        The reason provided by the user for the lock change
    user : User
        The user

    Returns
    -------
    LockInformation
        Updated lock information

    Raises
    ------
    HTTPException
        If the resource is not locked = 400
    """

    # If the resource is already locked then raise an error
    if not lock_information.locked:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unlock already unlocked resource."
        )

    # Apply the change to the resource

    # Unlock it
    lock_information.locked = False

    # Add history
    lock_information.history.append(
        LockEvent(
            action_type=LockActionType.UNLOCK,
            username=user.username,
            email=user.email,
            reason=reason,
            timestamp=int(datetime.now().timestamp())
        )
    )

    # return updated resource
    return lock_information


def seed_lock_configuration(id: str, config: Config) -> None:
    # default lock info
    lock_information = generate_default_lock_information()

    # double check there isn't a record already
    entry_exists = True

    # this should fail
    try:
        entry = get_lock_entry(id=id, config=config)
    except KeyError:
        entry_exists = False

    if entry_exists:
        raise HTTPException(
            status_code=500,
            detail=f"While seeding an item, the lock configuration already existed for that handle. Unexpected state. {id=}. Contact admin."
        )

    # now create the record
    lock_entry = LockTableEntry(
        id=id,
        lock_information=lock_information
    )

    # write
    try:
        write_lock_table_entry(
            lock_entry=lock_entry,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write default lock configuration, error: {e}. Contact admin."
        )
