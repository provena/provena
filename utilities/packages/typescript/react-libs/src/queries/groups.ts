import { AUTH_API_ENDPOINTS } from "./endpoints";
import {
    ListGroupsResponse,
    ListUserMembershipResponse,
} from "../shared-interfaces/AuthAPI";
import { requests } from "../stores";
import { requestErrToMsg } from "../util/util";

export const fetchGroupList = () => {
    // List groups endpoint
    const endpoint = AUTH_API_ENDPOINTS.LIST_GROUPS;
    return requests
        .get(endpoint, {})
        .then((res) => {
            const resJson = res as ListGroupsResponse;
            if (!resJson.status.success) {
                Promise.reject(res);
            }
            return resJson;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const fetchUserGroups = () => {
    // List groups endpoint
    const endpoint = AUTH_API_ENDPOINTS.LIST_USER_MEMBERSHIP;
    return requests
        .get(endpoint, {})
        .then((res) => {
            const resJson = res as ListUserMembershipResponse;
            if (!resJson.status.success) {
                Promise.reject(res);
            }
            return resJson;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};
