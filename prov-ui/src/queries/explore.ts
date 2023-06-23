import { PROV_API_ENDPOINTS, requestErrToMsg, requests } from "react-libs";
import { LineageResponse } from "../shared-interfaces/ProvenanceAPI";

export const exploreCombined = (id: string) => {
    // params is the same for upstream and downstream
    const params = {
        starting_id: id,
        depth: 1,
    };

    const downstreamEndpoint = PROV_API_ENDPOINTS.EXPLORE_DOWNSTREAM;
    const upstreamEndpoint = PROV_API_ENDPOINTS.EXPLORE_UPSTREAM;

    return Promise.all([
        // Make downstream and upstream request
        requests
            .get(downstreamEndpoint, params)
            .then((res) => {
                const resJson = res as LineageResponse;
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
            }),
        requests
            .get(upstreamEndpoint, params)
            .then((res) => {
                const resJson = res as LineageResponse;
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
            }),
    ]);
};
