import { RegistryFetchResponse } from "../shared-interfaces/DataStoreAPI";
import { DATA_STORE_API_ENDPOINTS } from "./endpoints";
import { requests } from "../stores/apiagent";
import { requestErrToMsg } from "../util/util";

export const fetchDataset = (
    handle: string
): Promise<RegistryFetchResponse> => {
    const endpoint = DATA_STORE_API_ENDPOINTS.FETCH_DATASET;
    const params = {
        handle_id: handle,
    };
    return requests
        .get(endpoint, params)
        .then((res) => {
            const resJson = res as RegistryFetchResponse;
            if (!resJson.status.success || resJson.item === undefined) {
                return Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};
