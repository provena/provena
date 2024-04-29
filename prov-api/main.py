from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import uvicorn  # type: ignore
from config import base_config, dispatch_cors
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
from routes.check_access import checks
from routes.model_run import model_run
from routes.explore import explore
from routes.admin import general_admin, restore_from_registry, graph_admin
from routes.bulk import templates
from typing import Dict
from ProvenaSharedFunctionality.SentryMonitoring import init_sentry
import sentry_sdk

# Setup app
app = FastAPI()
init_sentry(
    dsn=base_config.sentry_dsn if base_config.monitoring_enabled else None,
    environment=base_config.sentry_environment,
    release=base_config.git_commit_id,
)
sentry_sdk.set_tag("API", "prov")
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

app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])
app.include_router(model_run.router,
                   prefix="/model_run",
                   tags=["Model Runs"])
app.include_router(explore.router,
                   prefix="/explore",
                   tags=["Explore Lineage"])
app.include_router(templates.router,
                   prefix="/bulk",
                   tags=["CSV Template Tools"])

# Admin
app.include_router(
    general_admin.router,
    prefix="/admin",
    tags=['Admin']
)

# Admin restore from registry
app.include_router(
    restore_from_registry.router,
    prefix="/admin",
    tags=['Admin']
)

# Graph admin
app.include_router(
    graph_admin.router,
    prefix="/graph/admin",
    tags=['Graph admin']
)


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
