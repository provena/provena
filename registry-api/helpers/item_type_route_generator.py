from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import ProtectedRole
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency, get_user_context
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.RegistryModels import *
from helpers.action_helpers import *
from helpers.lock_helpers import *
from typing import Type, Optional, cast
from config import Config, get_settings
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import *
from helpers.workflow_helpers import *
from route_models import *


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
        route_config: RouteConfig,
) -> APIRouter:

    router = APIRouter()

    action: RouteActions
    action_config: RouteActionConfig

    def limited_access_role_check(protected_roles: ProtectedRole, route_action: RouteActions, config: Config) -> None:
        # find current route config
        action_config = ROUTE_ACTION_CONFIG_MAP[route_action]

        # pull out the route based limits or the model based limits
        route_limited: Optional[Roles] = action_config.limited_access_roles
        model_limited: Optional[Roles] = route_config.limited_access_roles.get(
            route_action) if route_config.limited_access_roles else None

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

    def enforce_user_link_check(action_enforcement: bool, type_enforcement: bool, user: User, config: Config, force_required: bool = False, username: Optional[str] = None) -> Optional[str]:
        """

        Queries auth API link service for the username.

        Uses the user's token and the user endpoint.

        If there is no linked ID or any other error occurs then the request is rejected.

        Args:
            user (User): The user who's token we should use
            config (Config): The config
            username (Optional[str]): By default, the user's username is used, but can override

        Raises:
            HTTPException: Various exceptions, 400 if missing link, 500 for comms errors
        """

        # route and subtype level enforcement (or forced bypass)
        if (action_enforcement and type_enforcement) or force_required:
            if config.enforce_user_links:
                possible_link = get_user_link(
                    user=user, username=username or user.username, config=config)

                # abort if no link
                if possible_link is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"In order to perform this operation you must link your User account to a Person in the registry."
                    )
                return possible_link
            else:
                if not config.test_mode:
                    raise Exception(
                        f"Not sure how to handle required username link while link service lookup is disabled. Need to be in test mode.")

                # mocked linked person id
                return "1234"
        else:
            return None

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
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method], path=action_config.path,
                          response_model=route_config.fetch_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def fetch_item(
            id: str,
            seed_allowed: bool = False,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.FETCH].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # this method ensures that the user has an appropriate fetch role
            response: GenericFetchResponse = fetch_helper(
                id=id,
                seed_allowed=seed_allowed,
                item_model_type=route_config.item_model_type,
                category=route_config.desired_category,
                subtype=route_config.desired_subtype,
                available_roles=route_config.available_roles,
                user=protected_roles.user,
                config=config,
                service_proxy=False
            )
            return route_config.fetch_response_type(
                **response.dict()
            )

    action = RouteActions.LIST
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=route_config.list_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def list_items(
            subtype_list_request: SubtypeListRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.LIST].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # fixed subtype filter - pass in other parameters
            filter_by = FilterOptions(
                item_subtype=route_config.desired_subtype,
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
                item_model_type=route_config.item_model_type,
                category=route_config.desired_category,
                subtype=route_config.desired_subtype,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                config=config,
            )

            # parse into specialised format
            return route_config.list_response_type(
                **generic_response.dict()
            )

    action = RouteActions.SEED
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.seed_response_type, f"Seed response type must be supplied for action {action}. Item category {route_config.desired_category} and subtype {route_config.desired_subtype}."

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=route_config.seed_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def seed_item(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.SEED].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            assert route_config.seed_response_type
            return route_config.seed_response_type(
                ** (await seed_item_helper(
                    category=route_config.desired_category,
                    subtype=route_config.desired_subtype,
                    default_roles=route_config.default_roles,
                    config=config,
                    user=protected_roles.user,
                    versioning_enabled=route_config.provenance_enabled_versioning
                )).dict()
            )

    action = RouteActions.VERSION
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=VersionResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def version(
            version_request: VersionRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> VersionResponse:
            """
            Runs a version versioning operation.

            This is only enabled on items in the ENTITY category.

            Versioning an item creates a new item, with a new ID, sharing the same domain info as the specified item.

            The version number is incremented, 
            """

            # Ensure prov versioning is enabled!
            if not route_config.provenance_enabled_versioning:
                raise HTTPException(
                    status_code=500,
                    detail=f"Version endpoint active without provenance versioning enabled. Error."
                )

            version_spinoff = not config.test_mode

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.VERSION,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.VERSION].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                force_required=version_spinoff,
                user=protected_roles.user,
                config=config
            )

            if version_spinoff and linked_person_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"You cannot perform version without having a linked person in the registry."
                )

            version_info = await version_helper(
                id=version_request.id,
                reason=version_request.reason,
                item_model_type=route_config.item_model_type,
                domain_info_type=route_config.item_domain_info_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                default_roles=route_config.default_roles,
                service_proxy=False,
                config=config
            )

            session_id = "1234"
            if version_spinoff:
                assert linked_person_id
                assert version_info.new_item

                session_id = await spinoff_version_job(
                    username=protected_roles.user.username,
                    new_item=cast(ItemBase, version_info.new_item),
                    version_request=version_request,
                    version_number=version_info.version_number,
                    from_id=version_request.id,
                    to_id=version_info.new_handle_id,
                    linked_person_id=linked_person_id,
                    item_subtype=route_config.desired_subtype,
                    config=config
                )

            return VersionResponse(
                new_version_id=version_info.new_handle_id,
                version_job_session_id=session_id
            )

    action = RouteActions.UPDATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.create_response_type, f"Create response type must be supplied for action {action}. Item category {route_config.desired_category} and subtype {route_config.desired_subtype}."

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=UpdateResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def update_item(
            id: str,
            replacement_domain_info: route_config.item_domain_info_type,  # type: ignore
            reason: Optional[str] = None,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> UpdateResponse:
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
                replacement_domain_info : route_config.item_domain_info_type
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.UPDATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=replacement_domain_info,
                    desired_category=route_config.desired_category,
                    desired_subtype=route_config.desired_subtype,
                    json_schema_override=route_config.json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return UpdateResponse(status=validate_resp.status)

            # check locked
            locked_check(
                id=id,
                config=config
            )

            # fetch the item
            fetch_response = retrieve_and_type_item(
                id=id,
                item_model_type=route_config.item_model_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                config=config
            )

            # Something went wrong
            if fetch_response.status_response is not None:
                return UpdateResponse(status=fetch_response.status_response.status)

            record = fetch_response.record
            record_type = fetch_response.record_type
            assert record
            assert record_type

            # This is a check for if we want the creation spinoff workflow
            creation_spinoff = route_config.provenance_enabled_versioning and\
                record_type == RecordType.SEED_ITEM and\
                not config.test_mode

            if creation_spinoff and linked_person_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"You cannot update a seed item to a complete item without having a linked person."
                )

            new_item = update_item_helper(
                id=id,
                record=record,
                record_type=record_type,
                reason=reason,
                replacement_domain_info=replacement_domain_info,
                item_model_type=route_config.item_model_type,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                config=config,
                service_proxy=False
            )

            # Customised response postfix
            if record_type == RecordType.SEED_ITEM:
                postfix = "Seeded item was updated to a complete item."
            if record_type == RecordType.COMPLETE_ITEM:
                postfix = "Complete item had it's contents updated."

            response = UpdateResponse(
                status=Status(
                    success=True,
                    details="Successfully applied update. " + postfix
                )
            )

            # Under the right conditions, spin off the creation job
            if creation_spinoff:
                assert linked_person_id
                session_id = await spinoff_creation_job(
                    linked_person_id=linked_person_id,
                    created_item=new_item,
                    username=protected_roles.user.username,
                    config=config
                )

                # update session ID in response
                response.register_create_activity_session_id = session_id

            return response

    action = RouteActions.REVERT
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=ItemRevertResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def revert_item(
            revert_request: ItemRevertRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.REVERT].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # check locked
            locked_check(
                id=revert_request.id,
                config=config
            )

            return revert_item_helper(
                id=revert_request.id,
                reason=revert_request.reason,
                history_id=revert_request.history_id,
                domain_info_type=route_config.item_domain_info_type,
                item_model_type=route_config.item_model_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                config=config
            )

    action = RouteActions.CREATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.create_response_type, f"Create response type must be supplied for action {action}. Item category {route_config.desired_category} and subtype {route_config.desired_subtype}."

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=route_config.create_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def create_item(
            item_domain_info: route_config.item_domain_info_type,  # type: ignore
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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
            # This is a check for if we want the creation spinoff workflow
            creation_spinoff = route_config.provenance_enabled_versioning and not config.test_mode

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.CREATE,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.CREATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                # Will throw an error if unlinked and versioning enabled
                force_required=creation_spinoff,
                user=protected_roles.user,
                config=config
            )

            # no specific access checks at an item role level are required for
            # creating new things

            # Validation
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=item_domain_info,
                    desired_category=route_config.desired_category,
                    desired_subtype=route_config.desired_subtype,
                    json_schema_override=route_config.json_schema_override,
                    config=config,
                )
                assert route_config.create_response_type
                if not validate_resp.status.success:
                    return route_config.create_response_type(
                        status=validate_resp.status
                    )

            # creation
            obj = await create_item_helper(
                item_domain_info=item_domain_info,
                item_model_type=route_config.item_model_type,
                category=route_config.desired_category,
                subtype=route_config.desired_subtype,
                default_roles=route_config.default_roles,
                user=protected_roles.user,
                config=config,
                versioning_enabled=route_config.provenance_enabled_versioning
            )
            dict_ver = obj.dict()
            assert route_config.create_response_type
            response = route_config.create_response_type.parse_obj(dict_ver)

            # Under the right conditions, spin off the creation job
            if creation_spinoff:
                assert linked_person_id
                assert response.created_item
                session_id = await spinoff_creation_job(
                    linked_person_id=linked_person_id,
                    created_item=cast(ItemBase, response.created_item),
                    username=protected_roles.user.username,
                    config=config
                )
                # update session ID in response
                response.register_create_activity_session_id = session_id

            return response

    action = RouteActions.SCHEMA
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=JsonSchemaResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def get_schema(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.SCHEMA].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            if route_config.json_schema_override:
                return JsonSchemaResponse(
                    status=Status(
                        success=True, details=f"Successfully returned manually overridden JSON schema."
                    ),
                    json_schema=route_config.json_schema_override
                )

            try:
                # Returns the JSON Schema of the domain info component
                # of the item
                json_schema: Dict[str,
                                  Any] = route_config.item_domain_info_type.schema()
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
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=UiSchemaResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def ui_schema(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.UI_SCHEMA].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            return UiSchemaResponse(
                status=Status(
                    success=True, details=f"Delivered UI Schema successfully"),
                ui_schema=route_config.ui_schema if route_config.ui_schema else {}
            )

    action = RouteActions.VALIDATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=StatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def validate(
            item: route_config.item_domain_info_type,  # type: ignore
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.VALIDATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            return validate_item_helper(
                item=item,
                desired_category=route_config.desired_category,
                desired_subtype=route_config.desired_subtype,
                config=config,
                json_schema_override=route_config.json_schema_override
            )

    action = RouteActions.AUTH_EVALUATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=DescribeAccessResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def evaluate_access(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> DescribeAccessResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_EVALUATE,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_EVALUATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # anyone can evaluate their access against a resource - even if limited
            # access roles apply

            # decode the user's access and respond
            return describe_access_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=route_config.available_roles
            )

    action = RouteActions.AUTH_CONFIGURATION_GET
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=AccessSettings,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def get_auth_configuration(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> AccessSettings:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_CONFIGURATION_GET,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[
                    RouteActions.AUTH_CONFIGURATION_GET].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # anyone can seek the authorisation configuration for a resource
            # regardless of limited access roles

            # check that the user has admin level permission into the resource and
            # return along the way
            return get_and_check_access_settings_helper(
                id=id,
                config=config,
                available_roles=route_config.available_roles,
                user=protected_roles.user,
                expected_subtype=route_config.desired_subtype,
                item_model=route_config.item_model_type
            )

    action = RouteActions.AUTH_CONFIGURATION_PUT
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=StatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def put_auth_configuration(
            id: str,
            settings: AccessSettings,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> StatusResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_CONFIGURATION_PUT,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[
                    RouteActions.AUTH_CONFIGURATION_PUT].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # anyone can seek the authorisation configuration for a resource
            # regardless of limited access roles

            # check that the user has admin level permission into the resource and update
            check_and_update_access_settings_helper(
                id=id,
                config=config,
                new_access_settings=settings,
                available_roles=route_config.available_roles,
                user=protected_roles.user,
                expected_subtype=route_config.desired_subtype,
                item_model=route_config.item_model_type
            )
            return StatusResponse(status=Status(
                success=True,
                details=f"Successfully updated the authorisation configuration for item {id=}."
            ))

    action = RouteActions.AUTH_ROLES
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=AuthRolesResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def get_auth_roles(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
        ) -> AuthRolesResponse:

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.AUTH_ROLES,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.AUTH_ROLES].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            return AuthRolesResponse(
                roles=list(
                    map(lambda role_name: ROLE_METADATA_MAP[role_name], route_config.available_roles))
            )

    action = RouteActions.LOCK
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=StatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def lock_resource(
            lock_request: LockChangeRequest,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCK].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # fetches lock config, checks perms, updates, pushes
            lock_resource_route_helper(
                lock_request=lock_request,
                config=config,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                expected_subtype=route_config.desired_subtype,
                item_model=route_config.item_model_type
            )

            # return success
            return StatusResponse(
                status=Status(
                    success=True, details="Resource locked successfully.")
            )

    action = RouteActions.UNLOCK
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=StatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def unlock_resource(
            unlock_request: LockChangeRequest,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.UNLOCK].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            # fetches lock config, checks perms, updates, pushes
            unlock_resource_route_helper(
                unlock_request=unlock_request,
                config=config,
                user=protected_roles.user,
                available_roles=route_config.available_roles,
                expected_subtype=route_config.desired_subtype,
                item_model=route_config.item_model_type
            )

            # return success
            return StatusResponse(
                status=Status(
                    success=True, details="Resource unlocked successfully.")
            )

    action = RouteActions.LOCK_HISTORY
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=LockHistoryResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def lock_history(
            id: str,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCK_HISTORY].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            return lock_history_route_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=route_config.available_roles
            )

    action = RouteActions.LOCKED
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=LockStatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def lock_status(
            id: str,
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.LOCKED].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

            return lock_status_route_helper(
                id=id,
                config=config,
                user=protected_roles.user,
                available_roles=route_config.available_roles
            )

    action = RouteActions.DELETE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=StatusResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def delete_item(
            id: str,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level))
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.DELETE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                config=config
            )

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
    difference is that these methods observe a required header which is an
    encrypted JSON object of the user's info.  This is helpful when objects are
    created which have ownership tied to the username. 

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
    route_config.limited_access_roles).
    '''

    action = RouteActions.PROXY_FETCH
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method], path=action_config.path,
                          response_model=route_config.fetch_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_fetch_item(
            id: str,
            seed_allowed: bool = False,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_FETCH].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            # this method ensures that the user has an appropriate fetch role
            response: GenericFetchResponse = fetch_helper(
                id=id,
                seed_allowed=seed_allowed,
                item_model_type=route_config.item_model_type,
                category=route_config.desired_category,
                subtype=route_config.desired_subtype,
                available_roles=route_config.available_roles,
                user=user,
                config=config,
                # even with updated user context - we still pass this through as
                # the user's token is not actually valid - for doing group
                # access checks we need to make api req
                service_proxy=True
            )
            return route_config.fetch_response_type(
                **response.dict()
            )

    action = RouteActions.PROXY_SEED
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.seed_response_type, f"Seed response type must be supplied for {action} route. Item category is {route_config.desired_category} and subtype is {route_config.desired_subtype}"

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=route_config.seed_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_seed_item(
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_SEED].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            assert route_config.seed_response_type
            return route_config.seed_response_type(
                ** (await seed_item_helper(
                    category=route_config.desired_category,
                    subtype=route_config.desired_subtype,
                    default_roles=route_config.default_roles,
                    config=config,
                    user=user,
                    versioning_enabled=route_config.provenance_enabled_versioning
                )).dict()
            )

    action = RouteActions.PROXY_UPDATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.create_response_type, f"Create response type must be supplied for {action} route. Item category is {route_config.desired_category} and subtype is {route_config.desired_subtype}"

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=UpdateResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_update_item(
            id: str,
            replacement_domain_info: route_config.item_domain_info_type,  # type: ignore
            reason: Optional[str] = None,
            bypass_item_lock: bool = False,
            exclude_history_update: bool = False,
            manual_grant: bool = False,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
        ) -> UpdateResponse:
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
                replacement_domain_info : route_config.item_domain_info_type
                    The new domain specific information for that record.
                exclude_history_update: bool , optional
                    For excluding the history update. This should be true iff
                    informaiton being updated is not user editable information
                    and therefore should not constitue a new (loose) "version"
                    for the user to view. This is set to true if release
                    information is updating during a release process.
                bypass_item_lock: bool
                    bypass item lock field is to enable bypass for actions
                    performed by other APIs. Specifically, to enable the
                    updating of release information in the domain info on a
                    resource which is locked. This is because users should be
                    able to request a dataset for release when it is locked.
                manual_grant: bool
                    If the authorised client (i.e. the data store API / prov
                    store API) has additional info about the user/context which
                    means the normal auth checks should be bypassed, this flag
                    can be used


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

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_UPDATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=replacement_domain_info,
                    desired_category=route_config.desired_category,
                    desired_subtype=route_config.desired_subtype,
                    json_schema_override=route_config.json_schema_override,
                    config=config,
                )

                if not validate_resp.status.success:
                    return UpdateResponse(status=validate_resp.status)

            # locked check
            if not bypass_item_lock:
                locked_check(
                    id=id,
                    config=config
                )

            # fetch the item
            fetch_response = retrieve_and_type_item(
                id=id,
                item_model_type=route_config.item_model_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                config=config
            )

            # Something went wrong
            if fetch_response.status_response is not None:
                return UpdateResponse(status=fetch_response.status_response.status)

            record = fetch_response.record
            record_type = fetch_response.record_type
            assert record
            assert record_type

            # This is a check for if we want the creation spinoff workflow
            creation_spinoff = route_config.provenance_enabled_versioning and\
                record_type == RecordType.SEED_ITEM and\
                not config.test_mode

            if creation_spinoff and linked_person_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"You cannot update a seed item to a complete item without having a linked person."
                )

            new_item = update_item_helper(
                id=id,
                record=record,
                record_type=record_type,
                reason=reason,
                replacement_domain_info=replacement_domain_info,
                item_model_type=route_config.item_model_type,
                user=user,
                available_roles=route_config.available_roles,
                config=config,
                service_proxy=True,
                exclude_history_update=exclude_history_update,
                # This is currently only used for review approval since the
                # review user may not have write permissions but needs to update
                # the record
                manual_grant=manual_grant
            )

            # Customised response postfix
            if record_type == RecordType.SEED_ITEM:
                postfix = "Seeded item was updated to a complete item."
            if record_type == RecordType.COMPLETE_ITEM:
                postfix = "Complete item had it's contents updated."

            response = UpdateResponse(
                status=Status(
                    success=True,
                    details="Successfully applied update. " + postfix
                )
            )

            # Under the right conditions, spin off the creation job
            if creation_spinoff:
                assert linked_person_id
                session_id = await spinoff_creation_job(
                    linked_person_id=linked_person_id,
                    created_item=new_item,
                    username=user.username,
                    config=config
                )

                # update session ID in response
                response.register_create_activity_session_id = session_id

            return response

    action = RouteActions.PROXY_REVERT
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=ItemRevertResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_revert_item(
            revert_request: ItemRevertRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
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
                and history id. 

            Returns:
                ItemRevertResponse: Status response
            """

            # permission check for limited roles
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_REVERT,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_REVERT].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            # check locked
            locked_check(
                id=revert_request.id,
                config=config
            )

            return revert_item_helper(
                id=revert_request.id,
                reason=revert_request.reason,
                history_id=revert_request.history_id,
                domain_info_type=route_config.item_domain_info_type,
                item_model_type=route_config.item_model_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                user=user,
                available_roles=route_config.available_roles,
                config=config,
                service_proxy=True
            )

    action = RouteActions.PROXY_VERSION
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=VersionResponse,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_version(
            version_request: VersionRequest,
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
        ) -> VersionResponse:
            """
            Runs a version versioning operation in proxy mode. 

            This can only be accessed by the special set of service accounts, and it makes user access requests on behalf of the specified username.

            All subsequent jobs are owned by the specified proxy username.
            """

            # Ensure prov versioning is enabled!
            if not route_config.provenance_enabled_versioning:
                raise HTTPException(
                    status_code=500,
                    detail=f"Version endpoint active without provenance versioning enabled. Error."
                )

            version_spinoff = not config.test_mode

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_VERSION,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_VERSION].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                force_required=version_spinoff,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            if version_spinoff and linked_person_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"You cannot perform version without having a linked person in the registry."
                )

            version_info = await version_helper(
                id=version_request.id,
                reason=version_request.reason,
                item_model_type=route_config.item_model_type,
                domain_info_type=route_config.item_domain_info_type,
                correct_category=route_config.desired_category,
                correct_subtype=route_config.desired_subtype,
                user=user,
                available_roles=route_config.available_roles,
                default_roles=route_config.default_roles,
                service_proxy=True,
                config=config
            )

            # this is a mock session ID only relevant in test mode
            session_id = "1234"
            if version_spinoff:
                assert linked_person_id
                assert version_info.new_item

                # TODO validate that this user proxy information is sufficient
                session_id = await spinoff_version_job(
                    username=user.username,
                    new_item=cast(ItemBase, version_info.new_item),
                    version_request=version_request,
                    version_number=version_info.version_number,
                    from_id=version_request.id,
                    to_id=version_info.new_handle_id,
                    linked_person_id=linked_person_id,
                    item_subtype=route_config.desired_subtype,
                    config=config
                )

            return VersionResponse(
                new_version_id=version_info.new_handle_id,
                version_job_session_id=session_id
            )

    action = RouteActions.PROXY_CREATE
    action_config = ROUTE_ACTION_CONFIG_MAP[action]

    if action in route_config.desired_actions:
        assert route_config.create_response_type, f"Create response type must be supplied for {action} route. Item category is {route_config.desired_category} and subtype is {route_config.desired_subtype}"

        @router.api_route(methods=[action_config.method],
                          path=action_config.path,
                          response_model=route_config.create_response_type,
                          operation_id=action_config.op_id + route_config.library_postfix,
                          include_in_schema=not action_config.hide
                          )
        async def proxy_create_item(
            item_domain_info: route_config.item_domain_info_type,  # type: ignore
            config: Config = Depends(get_settings),
            protected_roles: ProtectedRole = Depends(
                get_correct_dependency(action_config.access_level)),
            # this looks for header as configured and decrypts
            proxy_user: ProtectedRole = Depends(get_user_context)
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

            # This is a check for if we want the creation spinoff workflow
            creation_spinoff = route_config.provenance_enabled_versioning and not config.test_mode

            # permission check
            limited_access_role_check(
                protected_roles=protected_roles,
                route_action=RouteActions.PROXY_CREATE,
                config=config
            )

            # enforce user link service
            linked_person_id = enforce_user_link_check(
                action_enforcement=ROUTE_ACTION_CONFIG_MAP[RouteActions.PROXY_CREATE].enforce_linked_owner,
                type_enforcement=route_config.enforce_username_person_link,
                # Will throw an error if unlinked and versioning enabled
                force_required=creation_spinoff,
                user=protected_roles.user,
                username=proxy_user.user.username,
                config=config
            )

            # use the proxy user - noting the token is not valid!
            user = proxy_user.user

            # no specific access checks at an item role level are required for
            # creating new things
            if config.perform_validation:
                validate_resp = validate_item_helper(
                    item=item_domain_info,
                    desired_category=route_config.desired_category,
                    desired_subtype=route_config.desired_subtype,
                    json_schema_override=route_config.json_schema_override,
                    config=config,
                )

                assert route_config.create_response_type
                if not validate_resp.status.success:
                    return route_config.create_response_type(
                        status=validate_resp.status
                    )

            assert route_config.create_response_type
            response = route_config.create_response_type(
                ** (await create_item_helper(
                    item_domain_info=item_domain_info,
                    item_model_type=route_config.item_model_type,
                    category=route_config.desired_category,
                    subtype=route_config.desired_subtype,
                    default_roles=route_config.default_roles,
                    user=user,
                    config=config,
                    versioning_enabled=route_config.provenance_enabled_versioning
                )).dict()
            )

            # Under the right conditions, spin off the creation job
            if creation_spinoff:
                assert linked_person_id
                assert response.created_item
                session_id = await spinoff_creation_job(
                    linked_person_id=linked_person_id,
                    created_item=cast(ItemBase, response.created_item),
                    username=user.username,
                    config=config
                )
                # update session ID in response
                response.register_create_activity_session_id = session_id

            return response

    # Return the generated router object
    return router
