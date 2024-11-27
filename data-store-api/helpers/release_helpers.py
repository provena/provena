from fastapi import HTTPException
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.DataStoreAPI import *
from KeycloakFastAPI.Dependencies import ProtectedRole
from config import Config
import boto3  # type: ignore
from helpers.auth_helpers import get_user_link, get_usernames_from_id  # type: ignore
from helpers.aws_helpers import setup_secret_cache
from helpers.auth_helpers import evaluate_user_access, evaluate_user_access_all
from helpers.util import timestamp
from helpers.email_builders import *
from interfaces.EmailClient import EmailClient
from typing import Callable

from helpers.registry_api_helpers import update_dataset_in_registry, user_fetch_dataset_from_registry, user_proxy_fetch_dataset_from_registry, get_user_email
from helpers.util import py_to_dict  # type: ignore

# Setup AWS secret cache (ensure you have AWS_DEFAULT_REGION if running locally)
secret_cache = setup_secret_cache()


def add_reviewer(reviewer_id: IdentifiedResource, config: Config) -> None:

    # TODO - verify the reviewer id belongs to a person entity
    # ok for now, admin only, similar level of precaution to manual
    # management in the console.

    try:
        ddb_resource = boto3.resource('dynamodb')
        reviewers_table = ddb_resource.Table(config.REVIEWERS_TABLE_NAME)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to connect to the reviewers database. Error: {e}")
        )

    try:
        reviewers_table.put_item(
            Item={
                'id': reviewer_id
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to add reviewer {reviewer_id} to the reviewers database. Error: {e}")
        )


def connect_to_table(table_name: str) -> Any:

    reviewers_table: Any
    try:
        ddb_resource = boto3.resource('dynamodb')
        reviewers_table = ddb_resource.Table(table_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to connect to the reviewers database. Error: {e}")
        )
    return reviewers_table


def delete_reviewer_by_id(reviewer_id: IdentifiedResource, config: Config) -> None:

    reviewers_table = connect_to_table(config.REVIEWERS_TABLE_NAME)

    try:
        reviewers_table.delete_item(
            Key={
                'id': reviewer_id
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to delete reviewer {reviewer_id} from the reviewers database. Error: {e}")
        )


def get_all_reviewers(config: Config) -> Set[IdentifiedResource]:

    reviewers_table = connect_to_table(config.REVIEWERS_TABLE_NAME)

    try:
        items = list_all_items_in_db(table=reviewers_table)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to list systems dataset reviewers. Error: {e}")
        )

    # just want to return the IDs
    return {item['id'] for item in items}


def list_all_items_in_db(
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


def validate_release_for_edit(dataset_item: ItemDataset) -> bool:
    """
    Validates that the dataset is not currently released or under review for
    release and therefore is valid for DATA edit.

    Parameters
    ----------
    dataset_item : ItemDataset
        The datset to validate

    Returns
    -------
    bool: true iff valid for DATA editing

    """
    return dataset_item.release_status not in [ReleasedStatus.PENDING, ReleasedStatus.RELEASED]


def validate_release_state_suitable_for_request(dataset_item: ItemDataset) -> bool:
    """
    Validates that the dataset is not currently released or under review and
    therefore a user should be able to request a review.

    Parameters
    ----------
    dataset_item : ItemDataset
        The datset to validate

    Returns
    -------
    bool: true iff valid for DATA editing

    """
    return dataset_item.release_status not in [ReleasedStatus.PENDING, ReleasedStatus.RELEASED]


IdUrlResolver = Callable[[str], str]


async def perform_approval_request(
    release_approval_request: ReleaseApprovalRequest,
    requester_id: str,
    datastore_url_resolver: IdUrlResolver,
    email_client: EmailClient,
    config: Config,
    protected_roles: ProtectedRole,
    user_cipher: str
) -> None:

    # It is assumed that user has data store write here as per API endpoint auth

    # validate user is admin of dataset

    # fetch dataset auth using registry API.
    dataset_id = release_approval_request.dataset_id
    dataset_fetch = user_fetch_dataset_from_registry(
        id=dataset_id,
        config=config,
        user=protected_roles.user
    )

    # raise 400 if admin not in roles
    if dataset_fetch.roles is None:
        raise HTTPException(
            status_code=401,
            detail=f"Failed to source roles for dataset with id {dataset_id}"
        )

    # Checks if ADMIN ROLE is present
    if not evaluate_user_access(
        user_roles=dataset_fetch.roles,
        acceptable_roles=[ADMIN_ROLE]
    ):
        raise HTTPException(
            status_code=401,  # unauthorised.
            detail=f"User {protected_roles.user.username} is not an admin of dataset {dataset_id}. Only admins of datasets can request" +
            " for the dataset to be reviewed."
        )

    # fetch dataset desired to be reviewed
    if dataset_fetch.item_is_seed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset {dataset_id} is a seed dataset. Seed datasets cannot be released.")
        )

    assert isinstance(dataset_fetch.item, ItemDataset)
    dataset_item: ItemDataset = dataset_fetch.item

    # validate data set is not already in review and not released (Pending State)
    valid_for_release = validate_release_state_suitable_for_request(
        dataset_item=dataset_item)
    if not valid_for_release:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset {dataset_id} is already pending review or is released. Cannot request a review while another is unresolved.")
        )

    # fetch list of system dataset reviewers and validate suggested user is in list of system dataset reviewers
    approver_id = release_approval_request.approver_id
    if approver_id not in get_all_reviewers(config=config):
        # raise 400
        raise HTTPException(
            status_code=400,
            detail=(f"User {approver_id} is not a system dataset reviewer. Please provide an ID for" +
                    " entity pointing to a person who is a valid dataset reviewer for this system.")
        )

    # validate desired reviewer has read permissions into the item use proxy
    # fetch with username of suggested reviewers. Person IDs can map to several
    # usernames for when a person is a member of multiple organisations.
    usernames = get_usernames_from_id(
        person_id=approver_id, config=config, secret_cache=secret_cache)

    # all usernames must have read perms into dataset. Raise error if any fail.
    for username in usernames:
        try:
            # this will catch not having metadata read. check again below and for dataset data read too.
            fetch_response = user_proxy_fetch_dataset_from_registry(
                item_id=dataset_id,
                config=config,
                proxy_username=username,
                secret_cache=secret_cache
            )
        except HTTPException as e:
            if e.status_code == 401:
                raise HTTPException(
                    status_code=400,
                    detail=(f"Desired reviewer '{username}' does not have read permissions into dataset {dataset_id}. Cannot request for dataset to be reviewed for release by a reviewer who cannot read it. Please provide {username} with dataset read and metadata read access to dataset for review.")
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch dataset {dataset_id} on behalf of user '{username}' through proxy whilst ensuring they have read access. Error: {e}")
        roles = fetch_response.roles
        assert roles, f'Failed to fetch roles for dataset {dataset_id} for through proxy request for user "{username}"'

        if not evaluate_user_access_all(
            required_roles=[DATASET_READ_ROLE, METADATA_READ_ROLE],
            user_roles=roles
        ):
            raise HTTPException(
                status_code=400,
                detail=(f"Desired reviewer '{username}' does not have read permissions into dataset {dataset_id}. Cannot request for dataset to be reviewed for release by a reviewer who cannot read it. Please provide {username} with dataset read and metadata read access to dataset for review.")
            )

    # done all neccessary checks
    # mark dataset as pending review and update its history
    dataset_item.release_status = ReleasedStatus.PENDING
    dataset_item.release_approver = release_approval_request.approver_id

    ts = timestamp()
    dataset_item.release_timestamp = ts
    dataset_item.release_history.append(
        ReleaseHistoryEntry(
            action=ReleaseAction.REQUEST,
            timestamp=ts,
            approver=release_approval_request.approver_id,
            requester=requester_id,
            notes=release_approval_request.notes,
        )
    )
    update_response = update_dataset_in_registry(
        user_cipher=user_cipher,
        id=dataset_id,
        config=config,
        # reason="Marking dataset as pending review",
        secret_cache=secret_cache,
        # re parse to only include the domain info
        domain_info=DatasetDomainInfo.parse_obj(py_to_dict(dataset_item)),
        exclude_history_update=True,
        # the user has been deemed an admin according to registry, no need for
        # override
        manual_grant=False
    )

    # create email to send to reviewer
    email_content = build_review_request_email(
        dataset_id=dataset_id,
        requester_id=requester_id,
        dataset_url=datastore_url_resolver(dataset_id),
        reason=release_approval_request.notes
    )

    reviewer_email = get_user_email(
        person_id=approver_id,
        secret_cache=secret_cache,
        config=config
    )

    # send email target is the requested reviewer
    try:
        await email_client.send_email(
            reason="Alerting requested dataset release reviewer", email_to=reviewer_email, email_content=email_content)
    except Exception as e:
        # TODO what to do when email fails - for now just throw error
        raise HTTPException(
            status_code=500,
            detail=f""
        )


async def perform_action_of_approval_request(
    action_approval_request: ActionApprovalRequest,
    datastore_url_resolver: IdUrlResolver,
    email_client: EmailClient,
    config: Config,
    protected_roles: ProtectedRole,
    user_cipher: str
) -> None:
    # validate user is a system reviewer and is assigned to review this dataset

    # fetch handle for this user's person entity using link service
    user_id = get_user_link(user=protected_roles.user, config=config)
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="In order to perform this operation you must link your User account to a Person in the registry."
        )

    # due diligence check to ensure the list of reviewers hasn't excluded since
    if user_id not in get_all_reviewers(config=config):
        raise HTTPException(
            status_code=401,
            detail="You are not a dataset reviewer. Only system dataset reviewers can perform this action. Contact system admins to request to be a reviewer."
        )

    # assumes that the reviewer has read access to the dataset
    dataset_id = action_approval_request.dataset_id
    dataset_fetch = user_fetch_dataset_from_registry(
        id=dataset_id,
        config=config,
        user=protected_roles.user
    )

    assert isinstance(dataset_fetch.item, ItemDataset)
    dataset_item: ItemDataset = dataset_fetch.item

    # check the dataset is in the correct state
    if dataset_item.release_status != ReleasedStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {dataset_id} is not pending review. Cannot perform this action."
        )

    # verify that the release approver matches the current user making request
    if dataset_item.release_approver != user_id:
        raise HTTPException(
            status_code=401,
            detail=f"User with name {protected_roles.user.username} and linked ID {user_id} is not the approver for dataset {dataset_id}. Only the designated approver can perform this action."
        )

    # update dataset domain info for release.
    dataset_item.release_status = ReleasedStatus.RELEASED if action_approval_request.approve else ReleasedStatus.NOT_RELEASED
    ts = timestamp()

    # TODO validate this behaviour

    # only include these is dataset is being approved for release
    # if action_approval_request.approve else None
    dataset_item.release_timestamp = ts
    # if action_approval_request.approve else None
    dataset_item.release_approver = user_id

    # leave "dataset_item.release_approver" as is regardless of it is is approved to show who the last denier was or the approver.

    dataset_item.release_history.append(
        ReleaseHistoryEntry(
            action=ReleaseAction.APPROVE if action_approval_request.approve else ReleaseAction.REJECT,
            timestamp=ts,
            approver=user_id,
            requester=None,
            notes=action_approval_request.notes,
        )
    )

    # make the update request
    try:
        update_response = update_dataset_in_registry(
            user_cipher=user_cipher,
            id=dataset_id,
            config=config,
            # reason="Marking dataset as pending review",
            secret_cache=secret_cache,
            # re parse to only include the domain info
            domain_info=DatasetDomainInfo.parse_obj(py_to_dict(dataset_item)),
            exclude_history_update=True,
            # the user is the marked reviewer, and carefully managed update, bypass auth
            manual_grant=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update release info for dataset {dataset_id} in the registry. Error: {e}")
        )

    # create email to send to reviewer
    email_content = build_review_actioned_email(
        dataset_id=dataset_id,
        reviewer_id=user_id,
        action=ReleaseAction.APPROVE if action_approval_request.approve else ReleaseAction.REJECT,
        dataset_url=datastore_url_resolver(dataset_id),
        notes=action_approval_request.notes
    )

    # TODO record the person who actually requested the review - not just assume owner username
    targets = [user_id]
    owner_username = dataset_item.owner_username
    try:
        owner_person_id = get_user_link(
            user=protected_roles.user, username=owner_username, config=config)
        if owner_person_id is not None:
            targets.append(owner_person_id)
    except Exception as e:
        print(f"Failed lookup of dataset owner using link service. Continuing without sending email.")

    emails = [get_user_email(
        person_id=target_id,
        secret_cache=secret_cache,
        config=config
    ) for target_id in targets]

    # send email target is the requested reviewer
    try:
        await email_client.send_emails(
            reason="Alerting dataset owner and release reviewer as to change in status",
            emails=[(email_to, email_content) for email_to in emails])
    except Exception as e:
        # TODO what to do when email fails - for now just throw error
        raise HTTPException(
            status_code=500,
            detail=f""
        )
