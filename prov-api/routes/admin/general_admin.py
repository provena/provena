from fastapi import APIRouter
from helpers.config_response import generate_config_route
router = APIRouter()

# Add the config route 
generate_config_route(
    router = router,
    # has admin prefix
    route_path = "/config"
)
