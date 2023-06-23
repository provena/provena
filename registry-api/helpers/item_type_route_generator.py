from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import ProtectedRole
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.RegistryModels import *
from helpers.action_helpers import *
from helpers.lock_helpers import *
from typing import TypeVar, Type, Optional
from config import Config, get_settings
from RegistrySharedFunctionality.RegistryRouteActions import *


SeedResponseTypeVar = TypeVar('SeedResponseTypeVar', bound=GenericSeedResponse)
FetchResponseTypeVar = TypeVar(
    'FetchResponseTypeVar', bound=GenericFetchResponse)
ListResponseTypeVar = TypeVar(
    'ListResponseTypeVar', bound=GenericListResponse)
CreateResponseTypeVar = TypeVar(
    'CreateResponseTypeVar', bound=GenericCreateResponse)
ItemDomainInfoTypeVar = TypeVar('ItemDomainInfoTypeVar', bound=DomainInfoBase)
ItemModelTypeVar = TypeVar('ItemModelTypeVar', bound=ItemBase)


def get_correct_dependency(level: RouteAccessLevel) -> Any:
    if level == RouteAccessLevel.READ:
        return read_user_protected_role_dependency
    if level == RouteAccessLevel.WRITE:
        return read_write_user_protected_role_dependency
    if level == RouteAccessLevel.ADMIN:
        return admin_user_protected_role_dependency
    raise ValueError(
        f"Cannot parse level: {level} to generate access dependency.")


def generate_router(
        desired_actions: List[RouteActions],
        desired_category: ItemCategory,
        desired_subtype: ItemSubType,
        item_model_type: Type[ItemModelTypeVar],
        item_domain_info_type: Type[ItemDomainInfoTypeVar],
        seed_response_type: Type[SeedResponseTypeVar],
        fetch_response_type: Type[FetchResponseTypeVar],
        create_response_type: Type[CreateResponseTypeVar],
        list_response_type: Type[ListResponseTypeVar],
        ui_schema: Optional[Dict[str, Any]],
        json_schema_override: Optional[Dict[str, Any]],
        library_postfix: str,
        available_roles: Roles,
        default_roles: Roles,
        enforce_username_person_link: bool,
        # if this entity type should only be usable via specific keycloak roles,
        # they can be added here - this is an ANY constraint
        limited_access_roles: Optional[Dict[RouteActions, Roles]] = None,
) -> APIRouter:
    router = APIRouter()

    action: RouteActions
    route_config: RouteActionConfig

    def limited_access_role_check(protected_roles: ProtectedRole, route_action: RouteActions, config: Config) -> None:
        # find current route config
        route_config = ROUTE_ACTION_CONFIG_MAP[route_action]

        # pull out the route based limits or the model based limits
        route_limited: Optional[Roles] = route_config.limited_access_roles
        model_limited: Optional[Roles] = limited_access_roles.get(
            route_action) if limited_access_roles else None

        if (route_limited or model_limited) and config.enforce_special_proxy_roles:
            # compile roles
            roles: Roles = []

            # generous policy based on combining access roles
            if route_limited:
                roles.extend(route_limited)
            if model_limited:
                roles.extend(model_limited)

            # permission check - ANY role
            authorised = special_permission_check(
                user=protected_roles.user,
                special_roles=roles
            )
            if not authorised:
                raise HTTPException(
                    status_code=401,
                    detail=f"You are not authorised to take this action."
                )

    def enforce_user_link_check(user: User, config: Config) -> None:
        """

        Queries auth API link service for the username.

        Uses the user's token and the user endpoint.

        If there is no linked ID or any other error occurs then the request is rejected.

        Args:
            user (User): The user - uses this username and token
            config (Config): The config

        Raises:
            HTTPException: Various exceptions, 400 if missing link, 500 for comms errors
        """
        possible_link = get_user_link(user=user, config=config)

        # abort if no link
        if possible_link is None:
            raise HTTPException(
                status_code=400,
                detail=f"In order to perform this operation you must link your User account to a Person in the registry."
            )

    def locked_check(
        id: str,
        config: Config
    ) -> None:
        """

        Checks the item identified by ID for lock status. 

        If error - throws error. 

        If locked - throws 401.

        Args:
            id (str): The item ID to check
            config (Config): The configuration

        """
        try:
            locked = get_lock_status(
                id=id,
                config=config
            )
        except HTTPException as he:
            raise HTTPException(
                status_code=he.status_code,
                detail=f"Failed to check if locked. No access provided. Error: {he.detail}."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error occurred. Failed to check if locked. No access provided. Error: {e}."
            )

        if locked:
            raise HTTPException(
                status_code=401,
                detail="Cannot perform this action as the resource is locked."
            )

    action = RouteActions.FETCH
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method], path=route_config.path,
                          response_model=fetch_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def fetch_item(
            id: str,
            seed_allowed: bool = False,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericFetchResponse:
            """    fetch_item
                Fetches the item specified by the id from the 
                registry. Only returns items which fit the specified
                item type in this route, or if you allow with the 
                seed_allowed flag, will return seed items of 
                matching category and subtype.

                Arguments
                ----------
                id : str
                    The handle id of the item to fetch.
                seed_allowed : bool, optional
                    Do you want to allow seed items to be returned, by default False

                Returns
                -------
                 : GenericFetchResponse
                    Returns a status and possibly the item.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """
            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.FETCH,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.FETCH].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # this method ensures that the user has an appropriate fetch role
            response: GenericFetchResponse = fetch_helper(
                id=id,
                seed_allowed=seed_allowed,
                item_model_type=item_model_type,
                category=desired_category,
                subtype=desired_subtype,
                available_roles=available_roles,
                user=protected_roles.user,
                config=config,
                service_proxy=False
            )
            return fetch_response_type(
                **response.dict()
            )

    action = RouteActions.LIST
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=list_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def list_items(
            subtype_list_request: SubtypeListRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level)),
        ) -> GenericListResponse:
            """    list_items
                Lists all items of the specified type (by route). Sorts items 
                into parsable complete entities (i.e. normal entities), parsable 
                seed items (i.e. incomplete), and completely unparsable entities. 

                If there are any unparsable entities, the success field of the return 
                status will be False, however the items will still be provided. 

                Arguments
                ----------

                Returns
                -------
                 : GenericListResponse
                    The list of items, sorted complete, seed and unparsable, as well 
                    as counts for each type.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.LIST,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.LIST].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # fixed subtype filter - pass in other parameters
            filter_by = FilterOptions(
                item_subtype=desired_subtype,
                record_type=subtype_list_request.filter_by.record_type if subtype_list_request.filter_by else QueryRecordTypes.COMPLETE_ONLY
            )
            sort_by = subtype_list_request.sort_by
            pagination_key = subtype_list_request.pagination_key
            page_size = subtype_list_request.page_size

            # get the paginated item list using a ddb query
            items, returned_pagination_key = list_items_paginated(
                table=get_registry_table(config=config),
                sort_by=sort_by,
                filter_by=filter_by,
                pagination_key=pagination_key,
                page_size=page_size,
            )

            # now use the auth and filter helper
            generic_response = item_list_validate_and_filter_helper(
                # pass through the items and pagination key
                items=items,
                pagination_key=returned_pagination_key,
                item_model_type=item_model_type,
                category=desired_category,
                subtype=desired_subtype,
                user=protected_roles.user,
                available_roles=available_roles,
                config=config,
            )

            # parse into specialised format
            return list_response_type(
                **generic_response.dict()
            )

    action = RouteActions.SEED
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=seed_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def seed_item(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericSeedResponse:
            """    seed_item
                Posts a new empty item. This will mint a handle, 
                set the creation time, and produce the correct 
                category and sub type. This can then be updated 
                later using the update endpoint.

                Arguments
                ----------

                Returns
                -------
                 : GenericSeedResponse
                    The seed item that was created.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """
            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.SEED,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.SEED].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return seed_response_type(
                ** (await seed_item_helper(
                    category=desired_category,
                    subtype=desired_subtype,
                    default_roles=default_roles,
                    config=config,
                    user=protected_roles.user
                )).dict()
            )

    action = RouteActions.UPDATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def update_item(
            id: str,
            replacement_domain_info: item_domain_info_type,  # type: ignore
            reason: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> StatusResponse:
            """    update_item
                PUT method to apply an update to an existing item. The existing
                item can either be a complete object/item or a seed item of
                matching category and subtype.

                To replace an item, you provide the id of the item as a query
                string alongside the domain information object that you want to
                update on that item. 

                Arguments
                ----------
                id : str
                    The id of the object in the registry. (Handle)
                replacement_domain_info : item_domain_info_type
                    The new domain specific information for that record.
                reason: Optional[str] = None
                    The reason for updating this item. If the item is a seed
                    item, there is no need to provide this field - it will be
                    ignored. If the item is a complete item then this field must
                    be provided.

                Returns
                -------
                 : StatusResponse
                    Was the update successful?

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.UPDATE,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.UPDATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=replacement_domain_info,
                    desired_category=desired_category,
                    desired_subtype=desired_subtype,
                    json_schema_override=json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return create_response_type(
                        status=validate_resp.status
                    )

            # check locked
            locked_check(
                id=id,
                config=config
            )

            return update_item_helper(
                id=id,
                reason=reason,
                replacement_domain_info=replacement_domain_info,
                item_model_type=item_model_type,
                correct_category=desired_category,
                correct_subtype=desired_subtype,
                user=protected_roles.user,
                available_roles=available_roles,
                config=config
            )

    action = RouteActions.REVERT
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=ItemRevertResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def revert_item(
            revert_request: ItemRevertRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> ItemRevertResponse:
            """
            Reverts the given item to the previous history version as
            identified by the history entry ID.

            Requires a reason for the reversion. 

            Checks the item is not locked and that the user is allowed to
            perform this reversion.

            Args:
                revert_request (ItemRevertRequest): Contains the id, reason and history id.

            Returns:
                ItemRevertResponse: Status response
            """
            # permission check for limited roles
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.REVERT,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.REVERT].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # check locked
            locked_check(
                id=revert_request.id,
                config=config
            )

            return revert_item_helper(
                id=revert_request.id,
                reason=revert_request.reason,
                history_id=revert_request.history_id,
                domain_info_type=item_domain_info_type,
                item_model_type=item_model_type,
                correct_category=desired_category,
                correct_subtype=desired_subtype,
                user=protected_roles.user,
                available_roles=available_roles,
                config=config
            )

    action = RouteActions.CREATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=create_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def create_item(
            item_domain_info: item_domain_info_type,  # type: ignore
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericCreateResponse:
            """    create_item
                POSTs a new item to the registry of the given item type. 
                The item does not need to include an id or creation time 
                as these will be automatically generated during creation.

                Responds with the successfully created item.

                If you want to seed an identity without providing full information,
                you can use the seed endpoint and then use the update endpoint later.

                Arguments
                ----------
                item : item_model_type
                    The item you want to create.

                Returns
                -------
                 : GenericCreateResponse
                    The create response which will include a status and the item 
                    created (if it was successful).

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.CREATE,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.CREATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # no specific access checks at an item role level are required for
            # creating new things

            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=item_domain_info,
                    desired_category=desired_category,
                    desired_subtype=desired_subtype,
                    json_schema_override=json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return create_response_type(
                        status=validate_resp.status
                    )

            obj = await create_item_helper(
                item_domain_info=item_domain_info,
                item_model_type=item_model_type,
                category=desired_category,
                subtype=desired_subtype,
                default_roles=default_roles,
                user=protected_roles.user,
                config=config,
            )
            dict_ver = obj.dict()
            response = create_response_type.parse_obj(dict_ver)
            return response

    action = RouteActions.SCHEMA
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=JsonSchemaResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def get_schema(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> JsonSchemaResponse:
            """    get_schema
                Returns the auto generated pydantic model 
                json schema. 

                This method uses only the domain info component of
                the item to ensure compliance with update and
                create endpoints. 

                This can be used to programmatically
                generate input forms, or to validate against the 
                pydantic model. You can also use the /validate 
                endpoint.

                Arguments
                ----------

                Returns
                -------
                 : SchemaResponse
                    Response with a json schema object.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.SCHEMA,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.SCHEMA].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            if json_schema_override:
                return JsonSchemaResponse(
                    status=Status(
                        success=True, details=f"Successfully returned manually overridden JSON schema."
                    ),
                    json_schema=json_schema_override
                )

            try:
                # Returns the JSON Schema of the domain info component
                # of the item
                json_schema: Dict[str, Any] = item_domain_info_type.schema()
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to extract json schema from the domain info pydantic model, exception{e}."
                )

            return JsonSchemaResponse(
                status=Status(
                    success=True, details=f"Successfully returned autogenerated pydantic model json schema."
                ),
                json_schema=json_schema
            )

    action = RouteActions.UI_SCHEMA
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=UiSchemaResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def get_ui_schema(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> UiSchemaResponse:
            """Returns the ui schema override provided for this model.

            This is for use by the front end - enabling overriding of specific
            model fields with specific components. 

            Parameters
            ----------
            protected_roles : ProtectedRole, optional
                _description_, by default Depends( read_user_protected_role_dependency)

            Returns
            -------
            UiSchemaResponse
                A JSON style mapping of field names (possibly nested) to component overrides.
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.UI_SCHEMA,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.UI_SCHEMA].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return UiSchemaResponse(
                status=Status(
                    success=True, details=f"Delivered UI Schema successfully"),
                ui_schema=ui_schema if ui_schema else {}
            )

    action = RouteActions.VALIDATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def validate(
            item: item_domain_info_type,  # type: ignore
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> StatusResponse:
            """    validate
                Validates the given item body input. If this method
                responds with a success, then a create_item call 
                with this input should succeed. Validates by ensuring 
                pydantic can parse the input, and some custom validation
                unique to item types.
                Arguments
                ----------
                item : item_model_type
                    The item which you want to validate

                Returns
                -------
                 : StatusResponse
                    Success or failure object.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.VALIDATE,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.VALIDATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return validate_item_helper(
                item=item,
                desired_category=desired_category,
                desired_subtype=desired_subtype,
                config=config,
                json_schema_override=json_schema_override
            )

    action = RouteActions.AUTH_EVALUATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=DescribeAccessResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def evaluate_access(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> DescribeAccessResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_EVALUATE,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_EVALUATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # anyone can evaluate their access against a resource - even if limited
            # access roles apply

            # decode the user's access and respond
            return describe_access_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=available_roles
            )

    action = RouteActions.AUTH_CONFIGURATION_GET
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=AccessSettings,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def get_auth_configuration(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> AccessSettings:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_CONFIGURATION_GET,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_CONFIGURATION_GET].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # anyone can seek the authorisation configuration for a resource
            # regardless of limited access roles

            # check that the user has admin level permission into the resource and
            # return along the way
            return get_and_check_access_settings_helper(
                id=id,
                config=config,
                available_roles=available_roles,
                user=protected_roles.user,
                expected_subtype=desired_subtype,
                item_model=item_model_type
            )

    action = RouteActions.AUTH_CONFIGURATION_PUT
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def put_auth_configuration(
            id: str,
            settings: AccessSettings,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> StatusResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_CONFIGURATION_PUT,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_CONFIGURATION_PUT].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # anyone can seek the authorisation configuration for a resource
            # regardless of limited access roles

            # check that the user has admin level permission into the resource and update
            check_and_update_access_settings_helper(
                id=id,
                config=config,
                new_access_settings=settings,
                available_roles=available_roles,
                user=protected_roles.user,
                expected_subtype=desired_subtype,
                item_model=item_model_type
            )
            return StatusResponse(status=Status(
                success=True,
                details=f"Successfully updated the authorisation configuration for item {id=}."
            ))

    action = RouteActions.AUTH_ROLES
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=AuthRolesResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def get_auth_roles(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> AuthRolesResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_ROLES,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_ROLES].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return AuthRolesResponse(
                roles=list(
                    map(lambda role_name: ROLE_METADATA_MAP[role_name], available_roles))
            )

    action = RouteActions.LOCK
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def lock_resource(
            lock_request: LockChangeRequest,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level)),
            config: Config = Depends(get_settings)
        ) -> StatusResponse:
            """
            lock_resource 

            Locks a resource. Requires general WRITE + resource ADMIN. 

            Parameters
            ----------
            id : str
                The ID of the resource
            reason : str
                A string explaining why this action was taken - included in logs

            Returns
            -------
            StatusResponse
                Successful response if everything works

            Raises
            ------
            HTTPException
                401 if any access exception
                400 if resource doesn't exist or if already locked
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.LOCK,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCK].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # fetches lock config, checks perms, updates, pushes
            lock_resource_route_helper(
                lock_request=lock_request,
                config=config,
                user=protected_roles.user,
                available_roles=available_roles,
                expected_subtype=desired_subtype,
                item_model=item_model_type
            )

            # return success
            return StatusResponse(
                status=Status(
                    success=True, details="Resource locked successfully.")
            )

    action = RouteActions.UNLOCK
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def unlock_resource(
            unlock_request: LockChangeRequest,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level)),
            config: Config = Depends(get_settings)
        ) -> StatusResponse:
            """
            unlock_resource 

            Unlocks a resource. Requires general write access as well as resource level
            admin access. 

            Parameters
            ----------
            id : str
                The ID of the resource
            reason : str
                A string explaining why this action was taken - included in logs

            Returns
            -------
            StatusResponse
                Successful response if everything works

            Raises
            ------
            HTTPException
                401 if any access exception
                400 if resource doesn't exist or if already unlocked
            """
            # Requires general write, and resource admin permission

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.UNLOCK,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.UNLOCK].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # fetches lock config, checks perms, updates, pushes
            unlock_resource_route_helper(
                unlock_request=unlock_request,
                config=config,
                user=protected_roles.user,
                available_roles=available_roles,
                expected_subtype=desired_subtype,
                item_model=item_model_type
            )

            # return success
            return StatusResponse(
                status=Status(
                    success=True, details="Resource unlocked successfully.")
            )

    action = RouteActions.LOCK_HISTORY
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=LockHistoryResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def lock_history(
            id: str,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level)),
            config: Config = Depends(get_settings)
        ) -> LockHistoryResponse:
            """
            lock_history 

            Fetches the history of locks for a resource. This information is already in
            the registry item payload and is therefore just a helper to pull out this
            info.

            You need data store read + data set metadata read to view the lock history.

            Parameters
            ----------
            handle_id : str
                The handle id of the resource

            Returns
            -------
            LockHistoryResponse
                Includes the lock history

            Raises
            ------
            HTTPException
                401 if any access exception
                400 if resource doesn't exist
            """
            # Requires general read + metadata read

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.LOCK_HISTORY,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCK_HISTORY].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return lock_history_route_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=available_roles
            )

    action = RouteActions.LOCKED
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=LockStatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def lock_status(
            id: str,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level)),
            config: Config = Depends(get_settings)
        ) -> LockStatusResponse:
            """
            lock_status 

            Returns whether an item is locked/unlocked.

            Requires general read permission and item specified metadata read.

            Parameters
            ----------
            id : str
                The id of the item

            Returns
            -------
            LockStatusResponse
            """

            # Requires general read + resource metadata read

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.LOCKED,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCKED].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return lock_status_route_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=available_roles
            )

    action = RouteActions.DELETE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def delete_item(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> StatusResponse:
            """    delete_item
                Admin only endpoint which can be used to delete 
                objects from the registry. Delete is by ID. This
                endpoint will return successfully even if the object
                doesn't exist in the first place.

                Arguments
                ----------
                id : str
                    The handle ID of the object to delete

                Returns
                -------
                 : StatusResponse
                    Was the deletion successful - returns true even if the item 
                    did not exist.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            #! TODO do we want owner/admins to be able to delete things?

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.DELETE,
                config=config
            )

            # possible link enforcement
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.DELETE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # locked check
            locked_check(
                id=id,
                config=config
            )

            return delete_item_helper(
                id=id,
                config=config
            )

    '''
    =============
    PROXY METHODS
    =============
    '''

    '''
    These methods are used when a service account acts on behalf of the user.
    They are not visible in the generated json schema/client libs. The
    difference is that these methods observe an optional 'username' query string
    parameter which overrides the User auth object. This is helpful when objects
    are created which have ownership tied to the username. 

    Access is checked via the following workflows
    
    - high level access check i.e. read/write/admin - this is on the token USER 
    - limited role access check (if applicable) - this is where service role is
      likely required e.g. data-store-api service role
    - for proxy seed/create - no other checks required. For proxy update - the
      proxy username (if provided) is used as the requesting user to ascertain
      access on a resource level. This decision is made so that the update
      operation through the data store API is still protected as if the user had
      created that resource.

    WARNING - these routes should be protected by a service role auth (see
    limited_access_roles).
    
    Currently only used for the data store - however the prov store might end up
    using a lot of these patterns as well.
    '''

    action = RouteActions.PROXY_FETCH
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method], path=route_config.path,
                          response_model=fetch_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def proxy_fetch_item(
            id: str,
            username: str,
            seed_allowed: bool = False,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericFetchResponse:
            """    fetch_item
                Fetches the item specified by the id from the 
                registry. Only returns items which fit the specified
                item type in this route, or if you allow with the 
                seed_allowed flag, will return seed items of 
                matching category and subtype.

                This checks the auth based on the username provided. 

                This route is only accessible via service accounts (i.e. other APIs.)

                Arguments
                ----------
                id : str
                    The handle id of the item to fetch.
                seed_allowed : bool, optional
                    Do you want to allow seed items to be returned, by default False

                Returns
                -------
                 : GenericFetchResponse
                    Returns a status and possibly the item.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """
            # permission check - proxy fetch should be accessible by all service accounts
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_FETCH,
                config=config
            )

            # update the user username based on service proxy username
            user = protected_roles.user
            user.username = username

            # possible link enforcement (post proxy username update)
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_FETCH].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # this method ensures that the user has an appropriate fetch role
            response: GenericFetchResponse = fetch_helper(
                id=id,
                seed_allowed=seed_allowed,
                item_model_type=item_model_type,
                category=desired_category,
                subtype=desired_subtype,
                available_roles=available_roles,
                user=user,
                config=config,
                service_proxy=True
            )
            return fetch_response_type(
                **response.dict()
            )

    action = RouteActions.PROXY_SEED
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=seed_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def proxy_seed_item(
            proxy_username: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericSeedResponse:
            """    seed_item
                Posts a new empty item. This will mint a handle, 
                set the creation time, and produce the correct 
                category and sub type. This can then be updated 
                later using the update endpoint.

                Arguments
                ----------

                Returns
                -------
                 : GenericSeedResponse
                    The seed item that was created.

                See Also (optional)
                --------

                Examples (optional)
                --------
            """
            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_SEED,
                config=config
            )

            # overwrite the username if provided
            if proxy_username is not None:
                protected_roles.user.username = proxy_username

            # possible link enforcement (post proxy username update)
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_SEED].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return seed_response_type(
                ** (await seed_item_helper(
                    category=desired_category,
                    subtype=desired_subtype,
                    default_roles=default_roles,
                    config=config,
                    user=protected_roles.user
                )).dict()
            )

    action = RouteActions.PROXY_UPDATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=StatusResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def proxy_update_item(
            id: str,
            replacement_domain_info: item_domain_info_type,  # type: ignore
            reason: Optional[str] = None,
            proxy_username: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> StatusResponse:
            """    update_item
                PUT method to apply an update to an existing item. The 
                existing item can either be a complete object/item or
                a seed item of matching category and subtype.

                To replace an item, you provide the id of the item as
                a query string alongside the domain information object
                that you want to update on that item. 

                Arguments
                ----------
                id : str
                    The id of the object in the registry. (Handle)
                replacement_domain_info : item_domain_info_type
                    The new domain specific information for that record.

                Returns
                -------
                 : StatusResponse
                    Was the update successful?

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_UPDATE,
                config=config
            )

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=replacement_domain_info,
                    desired_category=desired_category,
                    desired_subtype=desired_subtype,
                    json_schema_override=json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return create_response_type(
                        status=validate_resp.status
                    )

            # locked check
            locked_check(
                id=id,
                config=config
            )

            # overwrite the username if provided - this ensures that the proxied
            # user permissions are checked
            if proxy_username is not None:
                protected_roles.user.username = proxy_username

            # possible link enforcement (post proxy username update)
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_UPDATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return update_item_helper(
                id=id,
                replacement_domain_info=replacement_domain_info,
                reason=reason,
                item_model_type=item_model_type,
                correct_category=desired_category,
                correct_subtype=desired_subtype,
                user=protected_roles.user,
                available_roles=available_roles,
                config=config,
                service_proxy=True
            )

    action = RouteActions.PROXY_REVERT
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=ItemRevertResponse,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def proxy_revert_item(
            revert_request: ItemRevertRequest,
            proxy_username: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> ItemRevertResponse:
            """
            Reverts the given item to the previous history version as
            identified by the history entry ID.

            Requires a reason for the reversion. 

            Checks the item is not locked and that the user is allowed to
            perform this reversion.

            This is the proxy version for data store/prov api to make the update
            on behalf of the user.

            Args:
                revert_request (ItemRevertRequest): Contains the id, reason
                and history id. proxy_username (Optional[str]): The username of
                the proxy user - update will be under their username and access
                is checked for them.

            Returns:
                ItemRevertResponse: Status response
            """

            # permission check for limited roles
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_REVERT,
                config=config
            )

            # check locked
            locked_check(
                id=revert_request.id,
                config=config
            )

            # overwrite the username if provided - this ensures that the proxied
            # user permissions are checked
            if proxy_username is not None:
                protected_roles.user.username = proxy_username

            # possible link enforcement (post proxy username update)
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_REVERT].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            return revert_item_helper(
                id=revert_request.id,
                reason=revert_request.reason,
                history_id=revert_request.history_id,
                domain_info_type=item_domain_info_type,
                item_model_type=item_model_type,
                correct_category=desired_category,
                correct_subtype=desired_subtype,
                user=protected_roles.user,
                available_roles=available_roles,
                config=config,
                service_proxy=True
            )

    action = RouteActions.PROXY_CREATE
    route_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in desired_actions:
        @router.api_route(methods=[route_config.method],
                          path=route_config.path,
                          response_model=create_response_type,
                          operation_id=route_config.op_id + library_postfix,
                          include_in_schema=not route_config.hide
                          )
        async def proxy_create_item(
            item_domain_info: item_domain_info_type,  # type: ignore
            proxy_username: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(route_config.access_level))
        ) -> GenericCreateResponse:
            """    create_item
                POSTs a new item to the registry of the given item type. 
                The item does not need to include an id or creation time 
                as these will be automatically generated during creation.

                Responds with the successfully created item.

                If you want to seed an identity without providing full information,
                you can use the seed endpoint and then use the update endpoint later.

                Arguments
                ----------
                item : item_model_type
                    The item you want to create.

                Returns
                -------
                 : GenericCreateResponse
                    The create response which will include a status and the item 
                    created (if it was successful).

                See Also (optional)
                --------

                Examples (optional)
                --------
            """

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_CREATE,
                config=config
            )

            # overwrite the username if provided - created item will have
            # specified username as owner
            if proxy_username is not None:
                protected_roles.user.username = proxy_username

            # possible link enforcement (post proxy username update)
            enforce = ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_CREATE].enforce_linked_owner
            if config.enforce_user_links and enforce and enforce_username_person_link:
                enforce_user_link_check(
                    user=protected_roles.user, config=config)

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=item_domain_info,
                    desired_category=desired_category,
                    desired_subtype=desired_subtype,
                    json_schema_override=json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return create_response_type(
                        status=validate_resp.status
                    )

            return create_response_type(
                ** (await create_item_helper(
                    item_domain_info=item_domain_info,
                    item_model_type=item_model_type,
                    category=desired_category,
                    subtype=desired_subtype,
                    default_roles=default_roles,
                    user=protected_roles.user,
                    config=config,
                )).dict()

            )

    # Return the generated router object
    return router
