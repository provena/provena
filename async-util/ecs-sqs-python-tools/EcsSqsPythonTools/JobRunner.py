from EcsSqsPythonTools.Settings import JobBaseSettings
from ProvenaInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.Workflow import *
from datetime import datetime
from time import sleep
from EcsSqsPythonTools.Types import *

# 5 second wait time between polls
LOOP_POLL_WAIT = 5.0

# How many items to pull per poll
JOBS_PER_POLL = 1


def get_timestamp() -> float:
    return datetime.now().timestamp()


def continue_consuming(last_consumed_stamp: float, settings: JobBaseSettings) -> bool:
    """

    Determines if the poller should continue polling based on timeout etc.

    Args:
        last_consumed_stamp (float): The last timestamp when consumed

    Returns:
        bool: True iff continue consuming
    """
    print(f"Testing to determine if idle timeout reached.")
    idle_timeout = settings.idle_timeout
    current_stamp = get_timestamp()
    delta = current_stamp - last_consumed_stamp
    print(
        f"Current time: {current_stamp}, last consumed: {last_consumed_stamp}, delta: {delta}.")
    if (delta < idle_timeout):
        print(f"Delta < IDLE TIMEOUT {idle_timeout} so continuing...")
        return True
    else:
        print(f"Delta >= IDLE TIMEOUT {idle_timeout} so completing...")
        return False


def action_callback_response(task: ReceivedPayload, callback_response: CallbackResponse, settings: JobBaseSettings) -> None:
    """

    Actions the response from a dispatched function.

    Includes updating status table and responding to SQS queue.

    Args:
        task (ReceivedPayload): The task 
        callback_response (CallbackResponse): The response from callback
        settings (JobBaseSettings): Settings
    """
    print(f"Actioning callback response...")
    finish_work(queue_url=settings.queue_url, status_table_name=settings.status_table_name,
                received_payload=task, callback_response=callback_response)
    print(f"Finished actioning callback response")


def run_job_loop(callback: CallbackFunc, settings: JobBaseSettings) -> None:
    """

    Primary job loop runner.

    Polls for work according to specified timeouts and delays.

    Dispatches jobs to the runner.

    Args:
        callback (CallbackFunc): The function to dispatch to
        settings (JobBaseSettings): The settings
    """
    last_consumed_stamp = get_timestamp()
    work_found_last_round = False

    while continue_consuming(last_consumed_stamp, settings=settings):
        print(f"Polling for work...")

        # If job is pulled, then the status will be set to dequeued
        jobs = check_for_work(job_type=settings.job_type,
                              queue_url=settings.queue_url,
                              status_table_name=settings.status_table_name,
                              jobs_per_poll=JOBS_PER_POLL)

        if len(jobs) > 0:
            print(f"Work found.")
            work_found_last_round = True
            # for each item - execute job lifecycle
            for work in jobs:
                print(f"Work payload: {work}.")
                print(f"Updating last consumed timestamp")
                last_consumed_stamp = get_timestamp()

                # Mark as in progress

                # now mark the status item as dequeued
                update_job_status_table(
                    job_sns_payload=work.payload,
                    status=JobStatus.IN_PROGRESS,
                    table_name=settings.status_table_name,
                    info="Job has been dispatched to worker callback and is in progress."
                )

                print(f"Dispatching to work callback")
                callback_response: CallbackResponse
                try:
                    callback_response = callback(work.payload, settings)
                except Exception as e:
                    info = f"Callback function raised unhandled exception. Error: {e}."
                    callback_response = CallbackResponse(
                        status=JobStatus.FAILED,
                        info=info,
                        result=None
                    )
                print(f"Actioning workflow.")
                action_callback_response(
                    task=work, callback_response=callback_response, settings=settings)
                print(
                    f"Job lifecycle completed.")
        else:
            work_found_last_round = False
            print(
                f"No work found...waiting to poll again. Timeout: {LOOP_POLL_WAIT}.")

        if not work_found_last_round:
            print(f"Going to sleep...")
            sleep(LOOP_POLL_WAIT)
            print(f"Woke up...")
        else:
            print(f"Queue busy so not waiting before poll.")


def ecs_job_worker(worker_callback: CallbackFunc) -> None:
    """

    Main entry point for ECS worker.

    Register a callback which can handle jobs of the specific type.

    Sub type dispatching is handled by the caller.

    Args:
        worker_callback (CallbackFunc): The callback function.
    """
    print(f"Worker launched successfully")

    # setup job settings
    print("Loading env variables/settings...")
    settings = JobBaseSettings()
    print("Success")

    print("Starting job loop.")
    run_job_loop(callback=worker_callback, settings=settings)

    print("Completed job loop - shutting down exit 0")
