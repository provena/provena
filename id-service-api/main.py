from fastapi import FastAPI, Request
from mangum import Mangum
import uvicorn  # type: ignore
from config import base_config
from routes.admin import general_admin
from routes.check_access import checks
from routes.service import handle_service
from typing import Dict, Any
import random
import string
import logging
import time
from ProvenaSharedFunctionality.SentryMonitoring import init_sentry
import sentry_sdk

# Setup app
app = FastAPI()
init_sentry(
    dsn=base_config.sentry_dsn if base_config.monitoring_enabled else None,
    environment=base_config.sentry_environment,
    release=base_config.git_commit_id,
)
sentry_sdk.set_tag("API", "id-service")
sentry_sdk.set_tag("Environment", base_config.sentry_environment)

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)

# Logging middleware
# From https://philstories.medium.com/fastapi-logging-f6237b84ea64
@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    
    return response


# Get CORS middleware established

# Get the desired origins
assert base_config.stage

# Admin
app.include_router(
    general_admin.router,
    prefix="/admin",
    tags=['Admin']
)

# Basic access checks
app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])

# Handle service
app.include_router(handle_service.router, prefix="/handle",
                   tags=["Handle Service"])


@app.get("/", operation_id="root")
async def root() -> Dict[str, str]:
    """
    Function Description
    --------------------

    Demonstration unauthenticated endpoint.


    Returns
    -------
    Json
        Basic message response



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return {"message": "Health check successful."}


# Add lambda function
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
