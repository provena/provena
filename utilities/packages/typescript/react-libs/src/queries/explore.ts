import { QueryType } from "../hooks/useProvGraphData";
import { LineageResponse } from "../shared-interfaces/ProvenanceAPI";
import { requests } from "../stores";
import { requestErrToMsg } from "../util";
import { PROV_API_ENDPOINTS } from "./endpoints";

const SpecialQueryEndpointMap: Map<QueryType, string> = new Map([
    ["downstream_dataset", PROV_API_ENDPOINTS.DOWNSTREAM_DATASETS],
    ["upstream_dataset", PROV_API_ENDPOINTS.UPSTREAM_DATASETS],
    ["downstream_agent", PROV_API_ENDPOINTS.DOWNSTREAM_AGENTS],
    ["upstream_agent", PROV_API_ENDPOINTS.UPSTREAM_AGENTS],
]);

// This is used to ensure that references to query functions don't turn over, so
// that caching with react-query is handled properly

// Key := QueryType + ID
var StaticQueryMap: Map<string, Promise<LineageResponse>> = new Map([]);

export const specialExploreGeneric = (id: string, query: QueryType) => {
    // params is the same for upstream and downstream
    const params = {
        starting_id: id,
        depth: 4,
    };

    // The endpoint for this special prov query
    const endpoint = SpecialQueryEndpointMap.get(query)!;

    return requests
        .get(endpoint, params)
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
        });
};

type Direction = "upstream" | "downstream";

export const exploreDirect = (inputs: { id: string; direction: Direction }) => {
    // params is the same for upstream and downstream
    const params = {
        starting_id: inputs.id,
        depth: 1,
    };

    var endpoint = "";
    if (inputs.direction === "downstream") {
        endpoint = PROV_API_ENDPOINTS.EXPLORE_DOWNSTREAM;
    } else if (inputs.direction === "upstream") {
        endpoint = PROV_API_ENDPOINTS.EXPLORE_UPSTREAM;
    }

    // Make correct request
    return requests
        .get(endpoint, params)
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
        });
};

const TypeDispatchMap: Map<
    QueryType,
    (id: string) => Promise<LineageResponse>
> = new Map([
    [
        "explore_downstream",
        (id: string) => {
            return exploreDirect({ id: id, direction: "downstream" });
        },
    ],
    [
        "explore_upstream",
        (id: string) => {
            return exploreDirect({ id: id, direction: "upstream" });
        },
    ],
    [
        "downstream_dataset",
        (id) => {
            return specialExploreGeneric(id, "downstream_dataset");
        },
    ],
    [
        "upstream_dataset",
        (id) => {
            return specialExploreGeneric(id, "upstream_dataset");
        },
    ],
    [
        "downstream_agent",
        (id) => {
            return specialExploreGeneric(id, "downstream_agent");
        },
    ],
    [
        "upstream_agent",
        (id) => {
            return specialExploreGeneric(id, "upstream_agent");
        },
    ],
]);

export const queryDispatcher = (inputs: { id: string; query: QueryType }) => {
    // Check if there is a static function already resolved
    const key = inputs.query + inputs.id;
    const possibleResolvedFunction = StaticQueryMap.get(key);

    if (!!possibleResolvedFunction) {
        console.log(
            `Using resolved static function for query ${inputs.id} ${inputs.query}.`
        );
        return possibleResolvedFunction;
    }

    console.log(
        `No resolved static function for query ${inputs.id} ${inputs.query}.`
    );

    const dispatcher = TypeDispatchMap.get(inputs.query);
    if (dispatcher === undefined) {
        console.error(
            "There is no query dispatcher for the type " + inputs.query
        );
    } else {
        const func = dispatcher(inputs.id);
        console.log(
            `Storing generated static function for query ${inputs.id} ${inputs.query}.`
        );
        StaticQueryMap.set(key, func);
        return func;
    }
};
