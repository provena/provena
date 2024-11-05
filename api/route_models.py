from typing import TypeVar, List, Optional, Generic
from dataclasses import dataclass
from ProvenaInterfaces.RegistryAPI import *
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import RouteActions

SeedResponseTypeVar = TypeVar('SeedResponseTypeVar', bound=GenericSeedResponse)
FetchResponseTypeVar = TypeVar(
    'FetchResponseTypeVar', bound=GenericFetchResponse)
ListResponseTypeVar = TypeVar(
    'ListResponseTypeVar', bound=GenericListResponse)
CreateResponseTypeVar = TypeVar(
    'CreateResponseTypeVar', bound=GenericCreateResponse)
ItemDomainInfoTypeVar = TypeVar('ItemDomainInfoTypeVar', bound=DomainInfoBase)
ItemModelTypeVar = TypeVar('ItemModelTypeVar', bound=ItemBase)


@dataclass
class RouteConfig(Generic[ItemModelTypeVar,
                          ItemDomainInfoTypeVar,
                          SeedResponseTypeVar,
                          FetchResponseTypeVar,
                          CreateResponseTypeVar,
                          ListResponseTypeVar]):
    tags: List[str]

    # what actions should be enabled for this type
    desired_actions: List[RouteActions]
    desired_category: ItemCategory
    desired_subtype: ItemSubType

    # The following don't cooperate perfectly with
    # mypy - the arguments should be Classes which are
    # subclasses of the generic bases e.g. ItemBase
    # Generic<Action>Response etc.
    item_model_type: Type[ItemModelTypeVar]
    item_domain_info_type: Type[ItemDomainInfoTypeVar]
    seed_response_type: Optional[Type[SeedResponseTypeVar]]
    fetch_response_type: Type[FetchResponseTypeVar]
    create_response_type: Optional[Type[CreateResponseTypeVar]]
    list_response_type: Type[ListResponseTypeVar]

    # Specify a ui schema override which lets the
    # front end know how to render specific views
    ui_schema: Optional[Dict[str, Any]]
    json_schema_override: Optional[Dict[str, Any]]

    # client library route prefix
    library_postfix: str

    # authorisation roles
    available_roles: Roles
    default_roles: Roles

    # The user must have at least one of these roles for the API to accept
    # requests
    limited_access_roles: Optional[Dict[RouteActions, Roles]] = None

    # Should this item type enforce the user having a linked Person?
    enforce_username_person_link: bool = False

    # Should this subtype apply provenance enabled versioning?
    provenance_enabled_versioning: bool = False
