import requests as rq
from typing import TypeAlias, Callable, Any, Optional, Dict, List
from ProvenaInterfaces.AsyncJobAPI import *
from ProvenaInterfaces.RegistryAPI import ProvGraphRestoreResponse, ProvGraphRestoreRequest
import json
from ToolingEnvironmentManager.Management import PopulatedToolingEnvironment
import math
import time
from tqdm.asyncio import tqdm_asyncio as tqdm

# get some slow and fast sessions for efficiently querying the API for big jobs
# slow session is just used for job launches to not overwhelm job system
from helpers.util import slow_session, fast_session

GetAuthFunction: TypeAlias = Callable[[], Any]


async def fetch_item(
    id: str,
    auth: GetAuthFunction,
    registry_endpoint: str,
) -> Dict[str, Any]:
    endpoint = f"{registry_endpoint}/registry/general/fetch"
    params = {
        'id': id
    }
    # parse response
    response = await fast_session.get(url=endpoint, params=params, auth=auth())

    assert response.status_code == 200, f"Status code: {response.status_code}, details {response.json()['detail']}."

    # parse as fetch response
    response_json = response.json()
    # check that succeeded
    assert response_json['status'][
        'success'], f"Non successful response, err: {response_json['status']['details']}"
    # get the item
    item: Dict[str, Any] = response_json['item']
    assert item
    return item


async def resolve_linked_person(
    username: str,
    auth: GetAuthFunction,
    auth_api_endpoint: str,
) -> str:
    endpoint = f"{auth_api_endpoint}/link/admin/lookup"
    params = {
        'username': username
    }
    # parse response

    response = await fast_session.get(url=endpoint, params=params, auth=auth())

    assert response.status_code == 200, f"Status code: {response.status_code}, details {response.json()['detail']}."

    # parse as fetch response
    response_json = response.json()
    # check that succeeded
    assert response_json['success'], f"User {username = } does not have linked Person"
    return response_json["person_id"]


async def launch_job(request_payload: AdminLaunchJobRequest, auth: GetAuthFunction, endpoint: str) -> AdminLaunchJobResponse:
    endpoint = f"{endpoint}/jobs/admin/launch"
    response = await slow_session.post(
        url=endpoint,
        auth=auth(),
        json=request_payload.dict(exclude_none=True)
    )

    assert response.status_code == 200, f"Non 200 status for launch job, info: {response.text}. {response}"
    return AdminLaunchJobResponse.parse_obj(response.json())


async def fetch_job_status(session_id: str, auth: GetAuthFunction, endpoint: str) -> Optional[AdminGetJobResponse]:
    endpoint = f"{endpoint}/jobs/admin/fetch"
    response = await fast_session.get(
        url=endpoint,
        params={'session_id': session_id},
        auth=auth(),
    )

    if response.status_code != 200:
        print(f"Non 200 status for fetch job, info: {response.text}.")
        return None

    return AdminGetJobResponse.parse_obj(response.json())


def gen_progress_bar(done: int, out_of: int, width: int = 20) -> str:
    count = math.floor((float(done) / float(out_of)) * float(width))
    return f"[{''.join(['#' for _ in range(count)])}{''.join(['-' for _ in range(width-count)])}]"


class JobListManager():
    """
    Class to manage the dispatching and monitoring of a collection of jobs.
    """
    item_id_to_job: Dict[str, AdminLaunchJobRequest]
    job_id_to_status: Dict[str, Optional[JobStatusTable]]
    job_id_to_item_id: Dict[str, str]
    auth: GetAuthFunction
    env: PopulatedToolingEnvironment

    def __init__(self, item_id_to_job: Dict[str, AdminLaunchJobRequest], auth: GetAuthFunction, env: PopulatedToolingEnvironment):
        self.item_id_to_job = item_id_to_job
        self.job_id_to_item_id = {}
        self.job_id_to_status = {}
        self.auth = auth
        self.env = env

    async def deploy_jobs(self) -> None:
        """
        Deploys the jobs by launching them using the job API and updating
        status, while displaying a progress bar in the console.
        """

        print("Starting deployment of jobs...")  # Print initial message

        # gather job list
        id_job_list = list(self.item_id_to_job.items())
        job_list = [launch_job(
            request_payload=job,
            auth=self.auth,
            endpoint=self.env.jobs_service_api_endpoint
        ) for _, job in id_job_list]

        # process job list
        print("Launching jobs in job pool")
        results = await tqdm.gather(*job_list)
        for res, id_job in zip(results, id_job_list):
            id, _ = id_job
            self.job_id_to_item_id[res.session_id] = id
            self.job_id_to_status[res.session_id] = None

        print("\nDeployment complete.")  # Print final message when done

    async def update_status(self) -> None:
        """
        Fetches status for all incomplete jobs and updates status dictionary.
        """
        # gather jobs
        session_ids = []

        for session_id, job_status in self.job_id_to_status.items():
            # already done
            if job_status is not None and (job_status.status == JobStatus.FAILED or job_status.status == JobStatus.SUCCEEDED):
                continue
            session_ids.append(session_id)

        job_list = [fetch_job_status(
            session_id=session_id,
            auth=self.auth,
            endpoint=self.env.jobs_service_api_endpoint
        ) for session_id in session_ids]

        # process jobs
        results = await tqdm.gather(*job_list)

        # store results
        for status_response, session_id in zip(results, session_ids):
            if status_response is not None:
                self.job_id_to_status[session_id] = status_response.job

    def display_status(self) -> None:
        """
        Prints the current status as a progress bar to the console.
        """
        succeeded = 0
        failed = 0
        in_progress = 0
        pending = 0
        total = len(self.job_id_to_status)

        for id, job in self.job_id_to_status.items():
            if job is None:
                pending += 1
                continue
            if job.status == JobStatus.SUCCEEDED:
                succeeded += 1
                continue

            if job.status == JobStatus.FAILED:
                failed += 1
                continue

            if job.status == JobStatus.PENDING or job.status == JobStatus.DEQUEUED:
                pending += 1
                continue

            in_progress += 1

        prog_bar = gen_progress_bar(
            done=succeeded + failed,
            out_of=total,
            width=50
        )

        print(f"""
              Succeeded: {succeeded}; Failed: {failed}; In-Progress: {in_progress}; Pending: {pending}
              {prog_bar} 
              """)

    async def run_until_complete(self, refresh_interval: int = 2) -> None:
        """

        Timer loop which performs a status update followed by display until
        completion at the specified interval.

        Args:
            refresh_interval (int, optional): The number of seconds to sleep
            after each update. Defaults to 2.
        """
        done = False
        while not done:
            await self.update_status()
            self.display_status()

            # check if done
            for job in self.job_id_to_status.values():
                if job is None or not (job.status == JobStatus.SUCCEEDED or job.status == JobStatus.FAILED):
                    done = False
                    break
                done = True

            if not done:
                time.sleep(refresh_interval)
            else:
                print("COMPLETE")

    def error_report(self) -> List[str]:
        """

        Generates a list of nodes which experienced errors and prints out errors
        to console.

        Returns:
            List[str]: The list of node ids which experienced errors.
        """
        err_messages: List[str] = []
        err_ids: List[str] = []

        for job_id, job in self.job_id_to_status.items():
            assert job
            if job.status == JobStatus.FAILED:
                err_messages.append(
                    f"Session ID: {job_id}\nError: {job.info}"
                )
                err_ids.append(self.job_id_to_item_id[job_id])

        if len(err_messages) > 0:
            print("--- ERROR REPORT ---")
            for err in err_messages:
                print(err)
            return err_ids
        else:
            return []

def submit_graph_restore_request_print_response(
    env: PopulatedToolingEnvironment,
    payload: ProvGraphRestoreRequest,
    auth: GetAuthFunction,
) -> None:
    """
    Submit a request to the registry API to restore the provenance graph"""    

    restore_response = rq.post(
        url = env.registry_api_endpoint + "/admin/restore-prov-graph",
        data = payload.json(),
        auth=auth()
    )
    
    if restore_response.status_code != 200:
        print(f"Failed to submit restore graph request. Status code: {restore_response.status_code}\n\n")
        print(restore_response.content)
        return
    restore_resp: ProvGraphRestoreResponse = ProvGraphRestoreResponse.parse_obj(restore_response.json())
    print("Restore graph request submitted successfully. Response:")
    print(restore_resp.json(indent=4))