from fastapi import APIRouter, Depends
from helpers.config_response import generate_config_route
from config import base_config
from typing import Optional, Dict
from KeycloakFastAPI.Dependencies import User
from dependencies.dependencies import admin_user_protected_role_dependency

router = APIRouter()

# Add the config route 
generate_config_route(
    router = router,
    # has admin prefix
    route_path = "/config"
)

# Admin only sentry debug endpoint to ensure it is reporting events
@router.get("/sentry-debug", operation_id="test_sentry_reporting")
async def trigger_error(
    user: User = Depends(admin_user_protected_role_dependency)
) -> Optional[Dict[str, str]]:
    
    if base_config.monitoring_enabled and base_config.sentry_dsn:
        division_by_zero = 1 / 0
    else:
        return {
                "message": f"Monitoring is disabled by configuration. Not going to trigger fake error. " +
                    f"Monitoring enabled: {base_config.monitoring_enabled}, and required DSN: {base_config.sentry_dsn}."
            }
    return None