import {
    AuthRolesResponse,
    GeneralListRequest,
    GenericCreateResponse,
    GenericFetchResponse,
    ItemRevertRequest,
    ItemRevertResponse,
    PaginatedListResponse,
    VersionRequest,
    VersionResponse,
    SchemaResponse,
    StatusResponse,
    UiSchemaResponse,
    UntypedFetchResponse,
    ListUserReviewingDatasetsRequest,
    PaginatedDatasetListResponse,
} from "../shared-interfaces/RegistryAPI";
import {
    AccessSettings,
    DomainInfoBase,
    ItemSubType,
} from "../shared-interfaces/RegistryModels";
import { requests } from "../stores/apiagent";
import { subtypeActionToEndpoint } from "../util/endpointHelpers";
import { requestErrToMsg } from "../util/util";
import {
    DATA_STORE_API_ENDPOINTS,
    REGISTRY_STORE_GENERIC_API_ENDPOINTS,
} from "./endpoints";

export const generalList = (props: GeneralListRequest) => {
    const endpoint = REGISTRY_STORE_GENERIC_API_ENDPOINTS.PAGINATED_LIST;
    return requests
        .post(endpoint, props)
        .then((res) => {
            const resJson = res as PaginatedListResponse;
            if (!resJson.status.success) {
                Promise.reject(res);
            }
            return resJson;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const generalFetch = (handle: string) => {
    const endpoint = REGISTRY_STORE_GENERIC_API_ENDPOINTS.FETCH_ITEM;
    const params = {
        id: handle,
    };
    return requests
        .get(endpoint, params)
        .then((res) => {
            const resJson = res as UntypedFetchResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const fetchBySubtype = (
    handle: string,
    subtype: ItemSubType,
    seedAllowed: boolean = true
) => {
    const endpoint = subtypeActionToEndpoint("FETCH", subtype);
    const params = {
        id: handle,
        seed_allowed: seedAllowed,
    };
    return requests
        .get(endpoint, params)
        .then((res) => {
            const resJson = res as GenericFetchResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const getJsonSchema = (subtype: ItemSubType) => {
    const endpoint = subtypeActionToEndpoint("SCHEMA", subtype);
    return requests
        .get(endpoint, {})
        .then((res) => {
            return res as SchemaResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const getUiSchema = (subtype: ItemSubType) => {
    const endpoint = subtypeActionToEndpoint("UI_SCHEMA", subtype);
    return requests
        .get(endpoint, {})
        .then((res) => {
            return res as UiSchemaResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const updateItem = (inputs: {
    id: string;
    data: DomainInfoBase;
    subtype: ItemSubType;
    reason: string;
}) => {
    const endpoint = subtypeActionToEndpoint("UPDATE", inputs.subtype);
    return requests
        .put(endpoint, inputs.data, { id: inputs.id, reason: inputs.reason })
        .then((res) => {
            const resJson = res as StatusResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const createItem = (inputs: {
    data: DomainInfoBase;
    subtype: ItemSubType;
}) => {
    const endpoint = subtypeActionToEndpoint("CREATE", inputs.subtype);
    return requests
        .post(endpoint, inputs.data, {}, true)
        .then((res) => {
            const resJson = res as GenericCreateResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const revertItem = (inputs: {
    id: string;
    historyId: number;
    reason: string;
    subtype: ItemSubType;
}) => {
    // Revert process is the same for data store and registry - just different
    // endpoint
    var endpoint = "/";
    if (inputs.subtype !== "DATASET") {
        endpoint = subtypeActionToEndpoint("REVERT", inputs.subtype);
    } else {
        endpoint = DATA_STORE_API_ENDPOINTS.REVERT_METADATA;
    }
    return requests
        .put(
            endpoint,
            {
                id: inputs.id,
                history_id: inputs.historyId,
                reason: inputs.reason,
            },
            {}
        )
        .then((res) => {
            const resJson = res as ItemRevertResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const fetchAuthConfiguration = (
    id: string,
    itemSubtype: ItemSubType
) => {
    // Get the endpoint for this item type to fetch auth configuration
    const endpoint = subtypeActionToEndpoint("AUTH_CONFIGURATION", itemSubtype);

    // Specify the item ID
    const params = {
        id: id,
    };

    // Get the auth configuration
    return requests
        .get(endpoint, params)
        .then((res) => {
            return res as AccessSettings;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const updateAuthConfiguration = (
    id: string,
    itemSubtype: ItemSubType,
    settings: AccessSettings
) => {
    // Get the endpoint for this item type to fetch auth configuration
    const endpoint = subtypeActionToEndpoint("AUTH_CONFIGURATION", itemSubtype);

    // Specify the item ID
    const params = {
        id: id,
    };

    // Update the auth configuration
    return requests
        .put(endpoint, settings, params)
        .then((res) => {
            const resJson = res as StatusResponse;
            try {
                if (!resJson.status.success) {
                    return Promise.reject(res);
                } else {
                    return resJson;
                }
            } catch (e) {
                return Promise.reject(res);
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const fetchAvailableRoles = (itemSubtype: ItemSubType) => {
    // Get the endpoint for this item type to fetch auth configuration
    const endpoint = subtypeActionToEndpoint("AUTH_ROLES", itemSubtype);

    // Get the auth configuration
    return requests
        .get(endpoint, {})
        .then((res) => {
            return res as AuthRolesResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const createNewVersion = (inputs: {
    data: VersionRequest;
    subtype: ItemSubType;
}) => {
    // endpoint for datastore is different.
    var endpoint = "/";
    if (inputs.subtype !== "DATASET") {
        endpoint = subtypeActionToEndpoint("VERSION", inputs.subtype);
    } else {
        endpoint = DATA_STORE_API_ENDPOINTS.VERSION_DATASET;
    }
    return requests
        .post(endpoint, inputs.data, {})
        .then((res) => {
            return res as VersionResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const listApprovalRequests = (
    inputs: ListUserReviewingDatasetsRequest
) => {
    // Get approval requests list
    const endpoint = REGISTRY_STORE_GENERIC_API_ENDPOINTS.APPROVAL_REQUEST_LIST;

    return requests
        .post(endpoint, inputs)
        .then((res) => {
            return res as PaginatedDatasetListResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};
