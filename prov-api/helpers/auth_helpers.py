from KeycloakFastAPI.Dependencies import User
from SharedInterfaces.RegistryAPI import Roles
from dependencies.dependencies import user_is_admin

def special_permission_check(user: User, special_roles: Roles) -> bool:
    # only grants access if the user has ANY of the special roles OR is an admin
    user_roles = user.roles

    # check admin
    if user_is_admin(user):
        return True

    # check special roles
    for possible_special_role in special_roles:
        if possible_special_role in user_roles:
            return True
    return False
