from typing import TypeAlias, Callable
from KeycloakRestUtilities.TokenManager import BearerAuth

GetAuthFunction: TypeAlias = Callable[[], BearerAuth]
