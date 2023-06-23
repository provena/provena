from SharedInterfaces.AuthAPI import *
from typing import Set

def produce_username_set(group: UserGroup) -> Set[str]:
    return set(map(lambda u: u.username, group.users))
