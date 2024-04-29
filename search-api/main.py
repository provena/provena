from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import uvicorn  # type: ignore
from config import base_config, dispatch_cors
from routes.admin import general_admin
from routes.check_access import checks
import routes.search.entity_registry as entity_registry
from ProvenaSharedFunctionality.SentryMonitoring import init_sentry
import sentry_sdk
import json
# Deprecated as of merge

# import routes.search.data_store as data_store
# import routes.search.global_search as global_search

from typing import Dict

# Setup app
app = FastAPI()
init_sentry(
    dsn=base_config.sentry_dsn if base_config.monitoring_enabled else None,
    environment=base_config.sentry_environment,
    release=base_config.git_commit_id,
)
sentry_sdk.set_tag("API", "search")
sentry_sdk.set_tag("Environment", base_config.sentry_environment)

# Get CORS middleware established

# Get the desired origins
origin_info = dispatch_cors(stage=base_config.stage,
                            base_domain=base_config.domain_base)

# If it is an origin list
if isinstance(origin_info, list):
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origins=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])
# Otherwise it is an origin regex
else:
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origin_regex=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])

# Admin
app.include_router(
    general_admin.router,
    prefix="/admin",
    tags=['Admin']
)

# Basic access checks
app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])

# search routes
app.include_router(entity_registry.router, prefix="/search",
                   tags=["Entity Registry"])


# Deprecated as of merge
# app.include_router(data_store.router, prefix="/search", tags=["Data Store"])
# app.include_router(global_search.router, prefix="/search",
#                   tags=["Global"])


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
