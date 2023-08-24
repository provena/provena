from EcsSqsPythonTools.JobRunner import ecs_job_worker
from EcsSqsPythonTools.Settings import JobBaseSettings
from EcsSqsPythonTools.Types import CallbackResponse
from jobs.registry_jobs import job_dispatcher
from SharedInterfaces.AsyncJobModels import *


def worker_callback(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    print(f"WORKER LAUNCHED")
    print(f"Received job {payload}")
    print(f"Dispatching into job dispatcher")
    return job_dispatcher(payload=payload, settings=settings)


def run() -> None:
    print("Launched.")
    ecs_job_worker(worker_callback=worker_callback)
    print("Complete.")
