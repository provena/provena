from typing import Any
from config import Settings
from typing import Any, Dict, List, Optional, Set
from ProvenaInterfaces.AsyncJobModels import *
import json
import boto3  # type: ignore
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Live states - see
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle.html
BLOCKING_ECS_STATES = ["PENDING", "PROVISIONING", "ACTIVATING", "RUNNING"]


@dataclass
class RunningTaskInfo():
    # ECS task status
    status: str
    # This might not be present or non running states
    started_at: Optional[datetime] = None


@dataclass
class TasksRunningResponse():
    # is the task running
    is_running: bool
    # If so - identify a list of running tasks - each with created at time where present
    tasks: Optional[List[RunningTaskInfo]] = None


def tz_aware_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def determine_time_delta(target: datetime) -> timedelta:
    """

    Determins the timedelta between a target time and the current time

    Args:
        target (datetime): The target datetime

    Returns:
        timedelta: The resulting timedelta object
    """
    # get current time in UTC
    now = tz_aware_now()

    # use overloaded - operator for delta - both tzaware
    delta = now - target

    print(f"Observed delta during safety check of {delta}.")

    return delta


def determine_time_delta_cutoff(limit: timedelta, actual: timedelta) -> bool:
    """

    Returns true iff actual time delta  > limit

    Args:
        limit (timedelta): The limit
        actual (timedelta): The actual observed delta

    Returns:
        bool: True iff actual > limit
    """
    return actual > limit


# Actual required delta := idle_timeout - safety delta buffer
SAFETY_DELTA_BUFFER = 20


def should_run_safety_delta(idle_timeout_s: int, tasks: List[RunningTaskInfo], settings: Settings) -> bool:
    """

    Applies the safety logic to determine if the task should be started even
    though it is technically running. 

    This takes into account the delta between the ECS task actually completing
    internally vs when ECS CLI reports it's change from RUNNING state. 

    If there are multiple created at times, then use the NEWEST. This is the
    most conservative (:= least likely to run a task) because we only start new
    tasks when the task has been running greater than some amount.

    Otherwise you could end up with a series of repeated launches because one of
    the tasks is old but is staying alive due to a busy queue.

    Args:
        idle_timeout_s (int): The async job idle timeout

        tasks (List[RunningTaskInfo]): Info about the tasks including optional
        created at times. If created at time is None, defaults to now, which
        results in this function returning false

    Returns:
        bool: true iff the task SHOULD start based on this delta
    """
    assert len(tasks) > 0

    # Safety cutoff in case of runaway tasks
    if len(tasks) >= settings.max_task_scaling:
        print(f"Safety cutoff experienced due to runaway task chaining.")
        return False

    # Parse DTs or default to NOW - now means that the delta is effectively zero
    # from current, making the youngest task very young
    created_dts = list(
        map(lambda t: t.started_at if t.started_at else tz_aware_now(), tasks))

    # find the freshest task (newest = maximum datetime)
    max_dt = max(created_dts)

    # determine delta vs current
    actual_delta = determine_time_delta(target=max_dt)
    delta_cut_off = timedelta(seconds=idle_timeout_s - SAFETY_DELTA_BUFFER)
    time_greater_than_safety = determine_time_delta_cutoff(
        limit=delta_cut_off,
        actual=actual_delta
    )
    return time_greater_than_safety


def extract_sns_payloads(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """

    Pulls out the payloads from SNS subscription message.

    Args:
        event (Dict[str, Any]): The raw payload

    Returns:
        List[Dict[str, Any]]: The list of SNS data
    """
    # Get the records out

    payloads: List[Dict[str, Any]] = []

    records: Optional[List[Dict[str, Any]]] = event.get('Records')

    if records is None:
        print("Could not find any records in the payload...")
        return payloads

    for record in records:
        print(f"Processing record {record}")

        sns_payload: Optional[Dict[str, Any]] = record.get('Sns')

        if sns_payload is None:
            print(f"No sns payload found on the record. Continuing")
            continue

        # this is JSON encoded
        message = sns_payload.get('Message')

        if message is None:
            print(f"No message found in SNS payload, skipping")
            continue

        # parse the message as json
        try:
            payloads.append(json.loads(message))
        except Exception as e:
            print(f"Failed to parse json in message... error: {e}.")
            print("Skipping.")
            continue

    return payloads


def parse_payload(payload: Dict[str, Any]) -> Optional[JobSnsPayload]:
    """

    Parses payload into JobSNSPayload

    Args:
        payload (Dict[str, Any]): The raw payload

    Returns:
        Optional[JobSnsPayload]: Parsed version
    """
    try:
        return JobSnsPayload.parse_obj(payload)
    except Exception as e:
        print(f"Failed to parse message, payload {payload}. Exception: {e}.")
        return None


def parse_payloads(payloads: List[Dict[str, Any]]) -> List[JobSnsPayload]:
    # helper to parse a list
    return [x for x in map(parse_payload, payloads) if x is not None]


def get_task_dfn(job_type: JobType, settings: Settings) -> str:
    """

    Pulls the desired job type's task dfn.

    Args:
        job_type (JobType): JobType to pull
        settings (Settings): The settings where this is located

    Raises:
        Exception: Can't find the job type task dfn arn

    Returns:
        str: Task definition ARN to launch for this job type
    """
    if job_type == JobType.PROV_LODGE:
        return settings.prov_lodge_task_definition_arn
    elif job_type == JobType.REGISTRY:
        return settings.registry_task_definition_arn
    elif job_type == JobType.EMAIL:
        return settings.email_task_definition_arn
    else:
        raise Exception(
            f"Not sure how to process the job type: {job_type}. No settings task definition arn.")


def select_public_subnet(vpc_id: str) -> Optional[str]:
    """

    Finds any public subnet in the given VPC

    Args:
        vpc_id (str): The vpc id to look in

    Returns:
        Optional[str]: Subnet if found
    """
    ec2 = boto3.resource('ec2')
    vpc = ec2.Vpc(vpc_id)

    public_subnets = []

    for subnet in vpc.subnets.all():
        if subnet.map_public_ip_on_launch:
            public_subnets.append(subnet.id)

    if not public_subnets:
        return None

    # Select the first public subnet
    return public_subnets[0]


def check_tasks_running(task_definition_arn: str, cluster_arn: str) -> TasksRunningResponse:
    """

    Checks if a task is running already

    TODO improve scaling behaviour past 1

    Args:
        task_definition_arn (str): The task dfn ARN
        cluster_arn (str): The ECS cluster

    Returns:
        bool: True iff task is already running on that task dfn arn
    """
    # Create an ECS client
    ecs_client = boto3.client('ecs')

    # List tasks in the cluster
    response = ecs_client.list_tasks(cluster=cluster_arn)
    tasks = response['taskArns']

    if len(tasks) == 0:
        return TasksRunningResponse(is_running=False)

    # Describe tasks in the cluster (get status and task definition)
    response = ecs_client.describe_tasks(cluster=cluster_arn, tasks=tasks)

    matched_tasks: List[Dict[str, Any]] = []

    # Check if any running tasks have the specified task definition ARN
    for task in response['tasks']:
        if task['taskDefinitionArn'] == task_definition_arn:
            matched_tasks.append(task)

    # Now we want to filter for non blocked state tasks
    active_tasks = list(
        filter(lambda t: t['lastStatus'] in BLOCKING_ECS_STATES, matched_tasks))

    # if there are no active tasks - return such
    if len(active_tasks) == 0:
        return TasksRunningResponse(is_running=False)

    # now report info for each
    tasks = list(map(lambda t: RunningTaskInfo(
        status=t['lastStatus'], started_at=task.get('startedAt')), active_tasks))
    return TasksRunningResponse(is_running=True, tasks=tasks)


def launch_task_in_ecs_cluster(subnet_id: str, task_definition_arn: str, cluster_arn: str) -> None:
    """

    Uses the ECS run task operation in the specified
    - subnet
    - cluster

    with the specified task dfn

    Args:
        subnet_id (str): The subnet
        task_definition_arn (str): Task dfn
        cluster_arn (str): Cluster

    Raises:
        Exception: Something goes wrong
    """
    # Create an ECS client
    ecs_client = boto3.client('ecs')

    # Launch the task
    response = ecs_client.run_task(
        cluster=cluster_arn,
        launchType='FARGATE',
        taskDefinition=task_definition_arn,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [subnet_id],
                'assignPublicIp': 'ENABLED'
            }
        }
    )

    # Check if the task was successfully launched
    if response['tasks']:
        task_arn = response['tasks'][0]['taskArn']
        print(f"Task {task_arn} launched successfully.")
    else:
        raise Exception(
            f"Failed to initiate task with definition arn {task_definition_arn}")


def launch_for_task(type: JobType, subnet_id: str, settings: Settings) -> None:
    """

    Handles launching a new task for a given job type.

    Combines dispatching of the task dfn arn, checking if task is running, and launching.

    Args:
        type (JobType): The job type
        subnet_id (str): Subnet id (must be public)
        settings (Settings): The settings
    """
    task_definition_arn = get_task_dfn(job_type=type, settings=settings)
    cluster_arn = settings.cluster_arn

    # TODO Make this more sophisticated - this is basic scaling protection

    # This limits to 1 concurrent
    tasks_running = check_tasks_running(
        task_definition_arn=task_definition_arn, cluster_arn=cluster_arn)

    run_task = False

    # run task if either running AND exceeded safety delta OR not running
    if tasks_running.is_running:
        if tasks_running.tasks is None or len(tasks_running.tasks) == 0:
            print("Unexpected state in which tasks were marked as running but no tasks were provided. Handle by defaulting to running a task.")
            run_task = True
        else:
            print(
                f"There were {len(tasks_running.tasks)} tasks observed to be running.")
            run_task = should_run_safety_delta(
                idle_timeout_s=settings.idle_timeout,
                tasks=tasks_running.tasks,
                settings=settings
            )
    else:
        run_task = True

    if tasks_running.is_running:
        if run_task:
            print(
                f"The job type: {type} does have a task running already, \
            however it is within the delta safety margin and therefore another task will be launched.")
        else:
            print(
                f"The job type: {type} does have a task running already and no new task will be run")
    else:
        print(
            f"The job type: {type} does not have a task running already and so a new task will be run.")

    if run_task:
        print(
            f"Launching task for {type}. {subnet_id=} {task_definition_arn=} {cluster_arn=}")
        launch_task_in_ecs_cluster(
            subnet_id=subnet_id, task_definition_arn=task_definition_arn, cluster_arn=cluster_arn)


def handler(event: Any, context: Any) -> None:
    """

    Lambda handler which maps the SNS sub into a usable workflow.

    Args:
        event (Any): The lambda event
        context (Any): _

    Raises:
        Exception: If an error occurs during operation e.g. missing env variables
    """
    print(f"{event = }")

    try:
        settings = Settings()
    except Exception as e:
        print(f"Missing configuration values. Error: {e}.")

    # This function needs to take the SNS topic event and publish it into the job status DB

    # First - parse the SNS payload from the event
    payloads = extract_sns_payloads(event=event)

    # For each payload - parse into pydantic model
    parsed_payloads = parse_payloads(payloads)

    # Now we need to determine set of job types
    types: Set[JobType] = set([])
    for payload in parsed_payloads:
        types.add(payload.job_type)

    # get a suitable subnet ID
    subnet_id = select_public_subnet(vpc_id=settings.vpc_id)

    if subnet_id is None:
        raise Exception(
            f"Failed to find a public subnet within vpc id {settings.vpc_id}")

    assert subnet_id

    # For each type - ensure there is already the right task dfn running - if not then run one
    for type in types:
        launch_for_task(type=type, subnet_id=subnet_id, settings=settings)

    # Finished
    return
