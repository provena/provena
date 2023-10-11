import { REGISTRY_STORE_GENERIC_API_ENDPOINTS } from "../queries/endpoints";
import { ItemSubType } from "../shared-interfaces/RegistryModels";

type Action =
    | "FETCH"
    | "UPDATE"
    | "CREATE"
    | "LIST"
    | "SEED"
    | "VERSION"
    | "SCHEMA"
    | "UI_SCHEMA"
    | "VALIDATE"
    | "AUTH_EVALUATE"
    | "AUTH_CONFIGURATION"
    | "AUTH_ROLES"
    | "LOCK"
    | "UNLOCK"
    | "REVERT"
    | "LOCK_HISTORY";

const actionPostfixes: Map<Action, string> = new Map([
    ["FETCH", "/fetch"],
    ["UPDATE", "/update"],
    ["REVERT", "/revert"],
    ["CREATE", "/create"],
    ["LIST", "/list"],
    ["SEED", "/seed"],
    ["VERSION", "/version"],
    ["SCHEMA", "/schema"],
    ["UI_SCHEMA", "/ui_schema"],
    ["VALIDATE", "/validate"],
    ["AUTH_EVALUATE", "/auth/evaluate"],
    ["AUTH_CONFIGURATION", "/auth/configuration"],
    ["AUTH_ROLES", "/auth/roles"],
    ["LOCK", "/locks/lock"],
    ["UNLOCK", "/locks/unlock"],
    ["LOCK_HISTORY", "/locks/history"],
]);

const subtypeRoutePrefixes: Map<ItemSubType, string> = new Map([
    ["MODEL_RUN", "/registry/activity/model_run"],
    ["ORGANISATION", "/registry/agent/organisation"],
    ["PERSON", "/registry/agent/person"],
    ["MODEL", "/registry/entity/model"],
    ["MODEL_RUN_WORKFLOW_TEMPLATE", "/registry/entity/model_run_workflow"],
    ["DATASET_TEMPLATE", "/registry/entity/dataset_template"],
    ["DATASET", "/registry/entity/dataset"],
    ["CREATE", "/registry/activity/create"],
    ["VERSION", "/registry/activity/version"],
    ["STUDY", "/registry/activity/study"],
]);

export const subtypeActionToEndpoint = (
    action: Action,
    itemSubtype: ItemSubType
): string => {
    const subtypePrefix = subtypeRoutePrefixes.get(itemSubtype);
    const actionPostfix = actionPostfixes.get(action);
    return `${REGISTRY_STORE_GENERIC_API_ENDPOINTS.ROOT_URL}${subtypePrefix}${actionPostfix}`;
};
