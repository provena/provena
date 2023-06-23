from SharedInterfaces.DataStoreAPI import *
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends
from dependencies.dependencies import admin_user_protected_role_dependency
from helpers.config_response import generate_config_route

router = APIRouter()


# Add the config route
generate_config_route(
    router=router,
    # has admin prefix
    route_path="/config"
)
