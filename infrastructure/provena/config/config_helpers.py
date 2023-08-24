from typing import Dict, Optional, List, Set, Tuple, Any
from provena.config.config_class import *

DEPENDENCY_LINKS: Dict[ProvenaComponent, List[ProvenaComponent]] = {
    ProvenaComponent.WARMER: [
        # warmer depends on nothing and vice versa
    ],
    ProvenaComponent.NETWORKING: [
        # Networking has no dependencies
    ],
    ProvenaComponent.KEYCLOAK: [
        # Needs a vpc to deploy into
        ProvenaComponent.NETWORKING,
    ],
    ProvenaComponent.IDENTITY_SERVICE: [
        # Doesn't have any dependencies except keycloak (endpoint)
    ],
    ProvenaComponent.DATA_STORE: [
        ProvenaComponent.IDENTITY_SERVICE,
        ProvenaComponent.AUTH_API,
        ProvenaComponent.ENTITY_REGISTRY
    ],
    ProvenaComponent.LANDING_PAGE: [
        # The landing page links to other things but technically only consumes
        # the auth API
        ProvenaComponent.AUTH_API
    ],
    ProvenaComponent.AUTH_API: [
        # depends on the registry API
        ProvenaComponent.ENTITY_REGISTRY
    ],
    ProvenaComponent.SEARCH: [
        # It does expose search endpoints for the data store and registry but
        # optionally uses them - not going to consider a dependency
    ],
    ProvenaComponent.ENTITY_REGISTRY: [
        # Has no dependencies other than front end auth API
        ProvenaComponent.AUTH_API,
        # Depends on async job service
        ProvenaComponent.ASYNC_JOBS
    ],
    ProvenaComponent.PROV_STORE: [
        ProvenaComponent.AUTH_API,
        # uses the entity registry and data store intensively
        ProvenaComponent.ENTITY_REGISTRY,
        ProvenaComponent.DATA_STORE,
    ],
    ProvenaComponent.ASYNC_JOBS: [

    ]
}


def walk_dep_graph(start: ProvenaComponent, visited: Set[ProvenaComponent]) -> Set[ProvenaComponent]:
    neighbours = DEPENDENCY_LINKS[start]
    found: Set[ProvenaComponent] = set(visited)

    # traverse each neighbour recursively (and avoid looping)
    for neighbour in neighbours:
        found.add(neighbour)
        if neighbour not in visited:
            visited.add(neighbour)
            results = walk_dep_graph(start=neighbour, visited=visited)
            visited.remove(neighbour)
            found.update(results)

    return found


def check_dep(component_set: Set[ProvenaComponent]) -> Tuple[bool, Optional[str]]:
    visited: Set[ProvenaComponent] = set([])
    comp_list = list(component_set)
    visited.add(comp_list[0])
    for comp in comp_list:
        found = walk_dep_graph(
            start=comp,
            visited=visited
        )
        visited.update(found)

    missing = visited - component_set
    if len(missing) > 0:
        return False, f"Can't deploy the specified set of components, missing the dependency(s): {[comp.value for comp in missing]}."
    else:
        return (True, None)


def validate_dependencies(component_config: ComponentConfig) -> None:
    component_set: Set[ProvenaComponent] = set([])
    components: List[Optional[Any]] = [
        component_config.networking,
        component_config.keycloak,
        component_config.identity_service,
        component_config.data_store,
        component_config.landing_page,
        component_config.auth_api,
        component_config.search,
        component_config.entity_registry,
        component_config.prov_store,
        component_config.warmer,
        component_config.async_jobs
    ]
    for c in components:
        if c:
            component_set.add(c.component)

    # run the graph walk
    success, err_message = check_dep(
        component_set=component_set
    )

    if not success:
        raise ValueError(err_message)


def validate_config(config: ProvenaConfig) -> None:
    validate_dependencies(config.components)

    if not config.components.keycloak:
        if not config.general.keycloak_endpoints:
            raise ValueError(
                "Since keycloak component is not being deployed, a manual keycloak endpoint must be provided!")
    if config.deployment.feature_deployment:
        if not config.deployment.ticket_no:
            raise ValueError(
                "Cannot deploy a feature stack without providing a ticket_no property.")


stage_to_prefix_map: Dict[Stage, Optional[str]] = {
    Stage.TEST: "testing",
    Stage.DEV: "dev",
    Stage.STAGE: "stage",
    Stage.PROD: None,
}


def resolve_endpoints(config: ProvenaConfig) -> ResolvedDomainNames:
    # helper function which takes a base subdomain and merges with root zone name

    def subdomain_to_full(subdomain: str) -> str:
        # base name never changes
        base_name = config.dns.root_domain

        # all URLs in system are https
        protocol = "https://"

        if subdomain == "":
            return f"{protocol}{base_name}"
        else:
            return f"{protocol}{subdomain}.{base_name}"

    # work out keycloak endpoints
    keycloak_minimal = ""
    realm_name = ""
    if config.general.keycloak_endpoints:
        keycloak_minimal = config.general.keycloak_endpoints.minimal_endpoint
        realm_name = config.general.keycloak_endpoints.realm_name
    else:
        kc_config = config.components.keycloak
        assert kc_config
        keycloak_minimal = f"{subdomain_to_full(kc_config.domain)}/auth"
        realm_name = kc_config.realm_name

    return ResolvedDomainNames(
        # root
        root_domain=config.dns.root_domain,

        # apis
        data_store_api=subdomain_to_full(
            config.components.data_store.api_domain) if config.components.data_store else "",
        prov_api=subdomain_to_full(
            config.components.prov_store.api_domain) if config.components.prov_store else "",
        registry_api=subdomain_to_full(
            config.components.entity_registry.api_domain) if config.components.entity_registry else "",
        search_api=subdomain_to_full(
            config.components.search.api_domain) if config.components.search else "",
        auth_api=subdomain_to_full(
            config.components.auth_api.api_domain) if config.components.auth_api else "",
        warmer_api=subdomain_to_full(
            config.components.warmer.domain) if config.components.warmer else "",
        async_jobs_api=subdomain_to_full(
            config.components.async_jobs.job_api_domain) if config.components.async_jobs else "",

        # uis
        data_store_ui=subdomain_to_full(
            config.components.data_store.ui_domain) if config.components.data_store else "",
        prov_ui=subdomain_to_full(
            config.components.prov_store.ui_domain) if config.components.prov_store else "",
        registry_ui=subdomain_to_full(
            config.components.entity_registry.ui_domain) if config.components.entity_registry else "",
        landing_ui=subdomain_to_full(
            config.components.landing_page.ui_domain) if config.components.landing_page else "",

        # keycloak
        keycloak_minimal=keycloak_minimal,
        keycloak_realm_name=realm_name
    )
