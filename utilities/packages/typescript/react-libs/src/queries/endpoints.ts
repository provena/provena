/**
================
Static Endpoints
================
*/

/**
=============
API Endpoints
=============
*/

export const DATA_STORE_API_URL = import.meta.env.VITE_DATA_STORE_API_ENDPOINT;
export const AUTH_API_URL = import.meta.env.VITE_AUTH_API_ENDPOINT;
export const REGISTRY_STORE_API_URL = import.meta.env
    .VITE_REGISTRY_API_ENDPOINT;
export const SEARCH_API_URL = import.meta.env.VITE_SEARCH_API_ENDPOINT;
export const PROV_API_URL = import.meta.env.VITE_PROV_API_ENDPOINT;
export const KEYCLOAK_AUTH_ENDPOINT = import.meta.env
    .VITE_KEYCLOAK_AUTH_ENDPOINT;
export const WARMER_API_URL = import.meta.env.VITE_WARMER_API_ENDPOINT;
export const JOB_API_URL = import.meta.env.VITE_JOB_API_ENDPOINT;

/**
==================
System cross links
==================
*/
export const LANDING_PAGE_LINK = import.meta.env.VITE_LANDING_PAGE_LINK;
export const DATA_STORE_LINK = import.meta.env.VITE_DATA_STORE_LINK;
export const PROV_STORE_LINK = import.meta.env.VITE_PROV_STORE_LINK;
export const REGISTRY_LINK = import.meta.env.VITE_REGISTRY_LINK;

// These are deployment specific - configured in the CDK deployment
export const DOCUMENTATION_BASE_URL = import.meta.env
    .VITE_DOCUMENTATION_BASE_LINK;
export const CONTACT_US_BUTTON_LINK = import.meta.env.VITE_CONTACT_US_LINK;

export const LANDING_PAGE_LINK_PROFILE =
    LANDING_PAGE_LINK + "/profile?function=roles";

/**
===========
Enforcement
===========
*/

// Currently we only enforce the API endpoints being present

const required: Array<[string | undefined, string]> = [
    [AUTH_API_URL, "Auth API URL"],
    [DATA_STORE_API_URL, "Data Store API URL"],
    [REGISTRY_STORE_API_URL, "Registry API URL"],
    [SEARCH_API_URL, "Search API URL"],
    [PROV_API_URL, "Prov API URL"],
    [JOB_API_URL, "Job API URL"],
    [KEYCLOAK_AUTH_ENDPOINT, "Keycloak Auth Endpoint URL"],
    [WARMER_API_URL, "Lambda Function Warmer API URL"],
    [
        DOCUMENTATION_BASE_URL,
        "Documentation home page. The URL of the github pages base documentation.",
    ],
    [
        CONTACT_US_BUTTON_LINK,
        "Contact us button link. The URL that will open in a new tab when the contact us button is pressed.",
    ],
];

required.forEach(([url, desc]) => {
    if (!url) {
        throw new Error(
            `Cannot use shared library functionality without ${desc}.`
        );
    }
});

export const REGISTRY_STORE_GENERIC_API_ENDPOINTS = {
    ROOT_URL: REGISTRY_STORE_API_URL,
    // AUTHENTICATION
    CHECK_GENERAL_ACCESS:
        REGISTRY_STORE_API_URL + "/check-access/check-general-access",
    CHECK_READ_ACCESS:
        REGISTRY_STORE_API_URL + "/check-access/check-read-access",
    CHECK_WRITE_ACCESS:
        REGISTRY_STORE_API_URL + "/check-access/check-write-access",
    // GENERIC
    PAGINATED_LIST: REGISTRY_STORE_API_URL + "/registry/general/list",
    FETCH_ITEM: REGISTRY_STORE_API_URL + "/registry/general/fetch",
    // ENTITY DATASET
    APPROVAL_REQUEST_LIST:
        REGISTRY_STORE_API_URL + "/registry/entity/dataset/user/releases",
};

export const SEARCH_API_ENDPOINTS = {
    ROOT_URL: SEARCH_API_URL,
    SEARCH_REGISTRY: SEARCH_API_URL + "/search/entity-registry",
};

export const JOB_API_ENDPOINTS = {
    ROOT_URL: JOB_API_URL,

    // User endpoints
    USER_FETCH: JOB_API_URL + "/jobs/user/fetch",
    USER_LIST: JOB_API_URL + "/jobs/user/list",
    USER_LIST_BATCH: JOB_API_URL + "/jobs/user/list_batch",

    // Admin endpoints
    ADMIN_LIST: JOB_API_URL + "/jobs/admin/list",
    ADMIN_LIST_BATCH: JOB_API_URL + "/jobs/admin/list_batch",
    ADMIN_FETCH: JOB_API_URL + "/jobs/admin/fetch",
    ADMIN_LAUNCH_JOB: JOB_API_URL + "/jobs/admin/launch",
};

const userLinkPrefix = "/link/user";
export const AUTH_API_ENDPOINTS = {
    ROOT_URL: AUTH_API_URL,
    LIST_GROUPS: AUTH_API_URL + "/groups/user/list_groups",
    DESCRIBE_GROUP: AUTH_API_URL + "/groups/user/describe_group",
    LIST_USER_MEMBERSHIP: AUTH_API_URL + "/groups/user/list_user_membership",

    REQUEST_ACCESS_CHANGE: AUTH_API_URL + "/access-control/user/request-change",
    GENERATE_ACCESS_REPORT:
        AUTH_API_URL + "/access-control/user/generate-access-report",
    GET_FULL_USER_REQUEST_HISTORY:
        AUTH_API_URL + "/access-control/user/request-history",
    ADMIN_USER_REQUESTS:
        AUTH_API_URL + "/access-control/admin/all-request-history",
    ADMIN_DELETE_REQUEST: AUTH_API_URL + "/access-control/admin/delete-request",
    ADMIN_STATUS_CHANGE:
        AUTH_API_URL + "/access-control/admin/change-request-state",
    ADD_NOTE: AUTH_API_URL + "/access-control/admin/add-note",

    // User groups
    USER_LIST_GROUPS: AUTH_API_URL + "/groups/user/list_groups",
    USER_DESCRIBE_GROUP: AUTH_API_URL + "/groups/user/describe_group",
    USER_LIST_USER_MEMBERSHIP:
        AUTH_API_URL + "/groups/user/list_user_membership",

    // Groups admin
    ADMIN_LIST_GROUPS: AUTH_API_URL + "/groups/admin/list_groups",
    ADMIN_DESCRIBE_GROUP: AUTH_API_URL + "/groups/admin/describe_group",
    ADMIN_LIST_MEMBERS: AUTH_API_URL + "/groups/admin/list_members",
    ADMIN_LIST_USER_MEMBERSHIP:
        AUTH_API_URL + "/groups/admin/list_user_membership",
    ADMIN_CHECK_MEMBERSHIP: AUTH_API_URL + "/groups/admin/check_membership",
    ADMIN_ADD_MEMBER: AUTH_API_URL + "/groups/admin/add_member",
    ADMIN_REMOVE_MEMBER: AUTH_API_URL + "/groups/admin/remove_member",
    ADMIN_REMOVE_MEMBERS: AUTH_API_URL + "/groups/admin/remove_members",
    ADMIN_ADD_GROUP: AUTH_API_URL + "/groups/admin/add_group",
    ADMIN_REMOVE_GROUP: AUTH_API_URL + "/groups/admin/remove_group",
    ADMIN_UPDATE_GROUP: AUTH_API_URL + "/groups/admin/update_group",

    USER_LINK_LOOKUP: AUTH_API_URL + userLinkPrefix + "/lookup",
    USER_LINK_VALIDATE: AUTH_API_URL + userLinkPrefix + "/validate",
    USER_LINK_ASSIGN: AUTH_API_URL + userLinkPrefix + "/assign",
};

const SPECIAL_QUERY_BASE = PROV_API_URL + "/explore/special";
export const PROV_API_ENDPOINTS = {
    ROOT_URL: PROV_API_URL,
    REGISTER_MODEL_RUN_COMPLETE: PROV_API_URL + "/model_run/register",
    REGISTER_MODEL_RUN_BATCH: PROV_API_URL + "/model_run/register_batch",
    EXPLORE_UPSTREAM: PROV_API_URL + "/explore/upstream",
    EXPLORE_DOWNSTREAM: PROV_API_URL + "/explore/downstream",
    GENERATE_CSV_TEMPLATE: PROV_API_URL + "/bulk/generate_template/csv",
    CONVERT_CSV_TEMPLATE: PROV_API_URL + "/bulk/convert_model_runs/csv",
    SUBMIT_MODEL_RUNS: PROV_API_URL + "/model_run/register_batch",
    REGENERATE_FROM_BATCH: PROV_API_URL + "/bulk/regenerate_from_batch/csv",
    UPSTREAM_DATASETS: SPECIAL_QUERY_BASE + "/contributing_datasets",
    DOWNSTREAM_DATASETS: SPECIAL_QUERY_BASE + "/effected_datasets",
    UPSTREAM_AGENTS: SPECIAL_QUERY_BASE + "/contributing_agents",
    DOWNSTREAM_AGENTS: SPECIAL_QUERY_BASE + "/effected_agents",
};

export const DATA_STORE_API_ENDPOINTS = {
    ROOT_URL: DATA_STORE_API_URL,
    //Access check
    CHECK_GENERAL_ACCESS:
        DATA_STORE_API_URL + "/check-access/check-general-access",
    CHECK_READ_ACCESS: DATA_STORE_API_URL + "/check-access/check-read-access",
    CHECK_WRITE_ACCESS: DATA_STORE_API_URL + "/check-access/check-write-access",
    //Metadata
    VALIDATE_METADATA: DATA_STORE_API_URL + "/metadata/validate-metadata",
    METADATA_SCHEMA: DATA_STORE_API_URL + "/metadata/dataset-schema",
    //Register dataset
    MINT_DATASET: DATA_STORE_API_URL + "/register/mint-dataset",
    //Update metadata
    UPDATE_METADATA: DATA_STORE_API_URL + "/register/update-metadata",
    REVERT_METADATA: DATA_STORE_API_URL + "/register/revert-metadata",
    //Version
    VERSION_DATASET: DATA_STORE_API_URL + "/register/version",
    //Registry Items
    LIST_DATASETS: DATA_STORE_API_URL + "/registry/items/list",
    FETCH_DATASET: DATA_STORE_API_URL + "/registry/items/fetch-dataset",

    // Access
    DESCRIBE_ACCESS:
        DATA_STORE_API_URL + "/registry/access/describe-dataset-access",

    // GET_SCHEMA: API_URL_ROOT + '/dataset-schema',
    //Registry credentials
    GENERATE_READ_CREDENTIALS:
        DATA_STORE_API_URL +
        "/registry/credentials/generate-read-access-credentials",
    GENERATE_WRITE_CREDENTIALS:
        DATA_STORE_API_URL +
        "/registry/credentials/generate-write-access-credentials",

    // Release
    // Fetch system approvers list
    FETCH_APPROVERS_LIST: DATA_STORE_API_URL + "/release/sys-reviewers/list",
    // Post approval request
    APPROVAL_REQUEST: DATA_STORE_API_URL + "/release/approval-request",
    // Put approval action
    APPROVAL_ACTION: DATA_STORE_API_URL + "/release/action-approval-request",
};
