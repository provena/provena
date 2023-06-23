from typing import Callable
from KeycloakRestUtilities.TokenManager import BearerAuth

GetAuthFunction = Callable[[], BearerAuth]
