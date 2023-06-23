# Fast API
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import base_config, dispatch_cors

# Routes
from routes.check_access import checks
from routes.access_control import admin, user
from routes.admin import admin as general_admin
from routes.groups import admin as group_admin, user as group_users, import_export_restore
from routes.identity import user as link_user
from routes.identity import admin as link_admin

# App runner
from mangum import Mangum  # type: ignore
import uvicorn  # type: ignore

# Setup app
app = FastAPI()

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

# /access-check
app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])

# /access-control

# user access control /user
app.include_router(admin.router, prefix="/access-control",
                   tags=["Admin access control"])

# admin access control /admin
app.include_router(user.router, prefix="/access-control",
                   tags=["User access control"])

# general admin
app.include_router(general_admin.router, prefix="/admin", tags=["Admin"])

# groups
app.include_router(group_admin.router, prefix="/groups", tags=["Groups Admin"])
app.include_router(group_users.router, prefix="/groups", tags=["Groups User"])
app.include_router(import_export_restore.router, prefix="/groups/admin")

# username person link service
app.include_router(link_user.router, prefix="/link",
                   tags=["Person Link Service (User)"])
app.include_router(link_admin.router, prefix="/link",
                   tags=["Person Link Service (Admin)"])


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
handler = Mangum(app)  # type: ignore

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
