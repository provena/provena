from pydantic import BaseModel
from typing import Optional, List, Dict


def optional_override_prefixor(domain: str, prefix: str, override: Optional[str]) -> str:
    """

    Helper function which performs the API prefixing while being override aware. 

    If override supplied - uses it directly. 

    If not, prefixes with protocol and prefix suitably.

    Args:
        domain (str): The domain base
        prefix (str): The API prefix
        override (Optional[str]): The optional override

    Returns:
        str: The URL
    """
    if override is not None:
        return override
    else:
        if prefix != "":
            return f"https://{prefix}.{domain}"
        else:
            return f"https://{domain}"


class ReplacementField(BaseModel):
    # What is the id which must be specified in the CLI?
    id: str
    # How does this value appear in the overrides?
    key: str


ReplacementDict = Optional[Dict[str, str]]


class ToolingEnvironment(BaseModel):
    # Core values

    # What is the name of this environment?
    name: str
    # What is the Provena application stage?
    stage: str
    # What is the base domain e.g. demo.provena.io
    domain: str
    # What is the auth realm name?
    realm_name: str

    # In the specified overrides - are there any variables to replace? Specify
    # the key (in CLI) and the in text value to find/replace
    replacements: List[ReplacementField] = []

    # Overrides

    # Endpoints are auto generated but can be overrided

    # APIs
    datastore_api_endpoint_override: Optional[str]
    auth_api_endpoint_override: Optional[str]
    registry_api_endpoint_override: Optional[str]
    prov_api_endpoint_override: Optional[str]
    search_api_endpoint_override: Optional[str]
    search_service_endpoint_override: Optional[str]
    handle_service_api_endpoint_override: Optional[str]
    jobs_service_api_endpoint_override: Optional[str]

    # Keycloak
    keycloak_endpoint_override: Optional[str]

    # Defaults - overridable
    aws_region: str = "ap-southeast-2"


class PopulatedToolingEnvironment(ToolingEnvironment):
    # This is the populated set of CLI parameters
    parameters: ReplacementDict

    def validate_parameters(self) -> None:
        """

        Validates the replacements vs parameters. 

        Raises:
            ValueError: Parameters missing/undefined
            ValueError: Missing particular parameter id
        """
        if len(self.replacements) > 0:
            if self.parameters is None:
                raise ValueError(
                    "No replacements provided for an environment which requires parameters.")

            # have some replacements ready
            required = set([r.id for r in self.replacements])
            provided = set(self.parameters.keys())

            missing = required - provided

            if len(missing) > 0:
                raise ValueError(
                    f"Insufficient number of parameter replacements for ToolingEnvironment. Expected {len(required)} got {len(missing)}. Missing the following: {missing}.")

    def perform_replacement(self, target: str) -> str:
        """

        Replaces any parameters in place in the current populated parameter
        context for this endpoint.

        NOTE assumes validated set of replacements/parameters and doesn't handle
        error.

        Args:
            target (str): The target to perform replacement against.

        Returns:
            str: The resulting string (mutated)
        """
        self.validate_parameters()
        for replacement in self.replacements:
            target = target.replace(
                replacement.key, (self.parameters or {}).get(replacement.id))
        return target

    # Auto derived properties (using parameters)
    @property
    def search_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="search",
            override=self.search_api_endpoint_override
        ))

    @property
    def jobs_service_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="job-api",
            override=self.jobs_service_api_endpoint_override
        ))

    @property
    def handle_service_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="handle",
            override=self.handle_service_api_endpoint_override
        ))

    @property
    def search_service_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="search-service",
            override=self.search_service_endpoint_override
        ))

    @property
    def auth_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="auth-api",
            override=self.auth_api_endpoint_override
        ))

    @property
    def prov_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="prov-api",
            override=self.prov_api_endpoint_override
        ))

    @property
    def datastore_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="data-api",
            override=self.datastore_api_endpoint_override
        ))

    @property
    def registry_api_endpoint(self) -> str:
        return self.perform_replacement(optional_override_prefixor(
            domain=self.domain,
            prefix="registry-api",
            override=self.registry_api_endpoint_override
        ))

    @property
    def keycloak_endpoint(self) -> str:
        endpoint = ""
        if self.keycloak_endpoint_override is not None:
            endpoint = self.keycloak_endpoint_override
        else:
            endpoint = f"https://auth.{self.domain}/auth/realms/{self.realm_name}"
        return self.perform_replacement(endpoint)

    def get_endpoint_map(self) -> Dict[str, str]:
        # Helper function for the integration test wrapper
        return {
            "DATA_STORE_API_ENDPOINT": self.datastore_api_endpoint,
            "REGISTRY_API_ENDPOINT": self.registry_api_endpoint,
            "PROV_API_ENDPOINT": self.prov_api_endpoint,
            "AUTH_API_ENDPOINT": self.auth_api_endpoint
        }


class ToolingEnvironmentsFile(BaseModel):
    envs: List[ToolingEnvironment]
