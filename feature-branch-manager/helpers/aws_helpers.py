import boto3  # type: ignore
from typing import List, Any, Optional, Dict
from custom_types import *
from helpers.cli_helpers import *
from rich import print
from time import sleep

DEFAULT_STACK_LIMIT: Optional[int] = None
ALL_STATES = [
    'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'DELETE_COMPLETE', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_FAILED', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS', 'IMPORT_IN_PROGRESS', 'IMPORT_COMPLETE', 'IMPORT_ROLLBACK_IN_PROGRESS', 'IMPORT_ROLLBACK_FAILED', 'IMPORT_ROLLBACK_COMPLETE',
]
NO_DELETE_STATE = [
    'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_FAILED', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS', 'IMPORT_IN_PROGRESS', 'IMPORT_COMPLETE', 'IMPORT_ROLLBACK_IN_PROGRESS', 'IMPORT_ROLLBACK_FAILED', 'IMPORT_ROLLBACK_COMPLETE',
]


def get_stack(stack_name: str) -> Optional[Dict[str, Any]]:
    client = boto3.client('cloudformation')
    try:
        response = client.describe_stacks(**{
            'StackName': stack_name
        })
        assert len(response['Stacks']) == 1
        return response['Stacks'][0]
    except Exception as e:
        print(
            f"Couldn't find expected stack {stack_name}. Returning None. Exception: {e}.")


def get_stacks_by_name(names: List[str]) -> List[Dict[str, Any]]:
    stacks: List[Dict[str, Any]] = []
    for name in names:
        potential_stack = get_stack(name)
        if potential_stack:
            stacks.append(potential_stack)
    return stacks


def list_cfn_stacks(limit: Optional[int] = DEFAULT_STACK_LIMIT) -> List[Dict[str, Any]]:
    print(f"Listing Cloudformation stacks from AWS...")
    client = boto3.client('cloudformation')

    token: Optional[str] = None
    fetched: List[Any] = []

    while (len(fetched) < limit if limit else True):
        # Don't filter states - include all
        payload: Dict[str, Any] = {
            "StackStatusFilter": NO_DELETE_STATE
        }

        # include pagination if required
        if token is not None:
            payload['NextToken'] = token

        response = client.list_stacks(**payload)

        fetched.extend(response['StackSummaries'])
        if 'NextToken' in response:
            token = response['NextToken']
        else:
            break

    print(f"Listed {len(fetched)} stacks.")
    return fetched


def parse_stack_info(ticket_num: int, stack_type: StackType, stack_data: Dict[str, Any]) -> StackInfo:
    return StackInfo(
        stack_data=stack_data,
        ticket_num=ticket_num,
        stack_type=stack_type
    )


def parse_status(stack_data: StackData) -> CfnStatus:
    return CfnStatus[stack_data['StackStatus']]


def fetch_stack_data(stack_id: str) -> StackData:
    client = boto3.client('cloudformation')
    return client.describe_stacks(**{
        'StackName': stack_id
    })['Stacks'][0]


def is_deleted(status: CfnStatus) -> bool:
    return status == CfnStatus.DELETE_COMPLETE


in_progress_states = [
    CfnStatus.DELETE_IN_PROGRESS,
]

pending_states = [
    CfnStatus.CREATE_IN_PROGRESS,
    CfnStatus.CREATE_FAILED,
    CfnStatus.CREATE_COMPLETE,
    CfnStatus.ROLLBACK_IN_PROGRESS,
    CfnStatus.ROLLBACK_FAILED,
    CfnStatus.ROLLBACK_COMPLETE,
    CfnStatus.DELETE_FAILED,
    CfnStatus.UPDATE_IN_PROGRESS,
    CfnStatus.UPDATE_COMPLETE_CLEANUP_IN_PROGRESS,
    CfnStatus.UPDATE_COMPLETE,
    CfnStatus.UPDATE_ROLLBACK_IN_PROGRESS,
    CfnStatus.UPDATE_ROLLBACK_FAILED,
    CfnStatus.UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS,
    CfnStatus.UPDATE_ROLLBACK_COMPLETE,
    CfnStatus.REVIEW_IN_PROGRESS,
]

complete_states = [
    CfnStatus.DELETE_COMPLETE,
]


def status_note(status: CfnStatus) -> str:
    if status in complete_states:
        return "Deleted"
    if status in in_progress_states:
        return "In Progress"
    else:
        return "Pending..."


def run_delete_op(stack_id: str) -> None:
    print(f"Triggering delete for {stack_id}.")
    client = boto3.client('cloudformation')
    client.delete_stack(
        **{'StackName': stack_id}
    )


def manage_deletion_lifecycle(stacks: List[Dict[str, Any]], force: bool) -> None:
    # manages the deletion of a set of stacks

    # initially double check all!

    if not force:
        for stack in stacks:
            name = stack['StackName']
            response = yes_or_no(
                f"Are you sure you want to delete stack: {name}?")
            if not response:
                print("Aborting...")
                exit(1)
    else:
        print("Bypassing checks because --force was used.")

    # how many iterations?
    iteration = 0
    # seconds
    sleep_time = 15
    # timeout (in seconds)
    timeout = 60 * 60  # (one hour)

    in_progress: List[StackData] = stacks

    while (iteration * sleep_time) < timeout and len(in_progress) > 0:
        # increment iteration
        iteration += 1

        # fetch updates
        print(f"Fetching status for {len(in_progress)} stacks...")
        new_data = [fetch_stack_data(stack_id=data['StackId'])
                    for data in in_progress]

        # sort by status
        new_data.sort(key=lambda d: status_note(parse_status(d)))

        # displaying status
        for data in new_data:
            status = parse_status(data)
            current_status_display = status_note(status)
            print(
                f"[{current_status_display}] Stack: {data['StackName']}, Status: {status.value}.")

        for data in new_data:
            status = parse_status(data)
            stack_id = data['StackId']
            if not (status in complete_states or status in in_progress_states):
                # must be in pending
                run_delete_op(stack_id=stack_id)
            elif status in complete_states:
                # this is done! remove from in progress
                in_progress = list(
                    filter(lambda d: d['StackId'] != stack_id, in_progress))

        if len(in_progress) > 0:
            # displaying progress through timeout
            print(f"Timeout in {timeout - (iteration * sleep_time)} seconds.")

            # waiting
            print(f"Waiting {sleep_time} seconds...")
            sleep(sleep_time)

    if (iteration * sleep_time) >= timeout:
        print("TIMED OUT...")
    else:
        print("Finished!")
