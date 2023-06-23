import { useQueries, useQuery } from "@tanstack/react-query";
import { fetchBySubtype } from "../queries/registry";
import { GenericFetchResponse } from "../shared-interfaces/RegistryAPI";
import { ItemBase, ItemSubType } from "../shared-interfaces/RegistryModels";
import { LoadedEntity, combineLoadStates } from "../interfaces/hookInterfaces";
import { mapQueryToLoadedEntity } from "../interfaces/hookInterfaces";
import { fetchRegistryItem } from "../queries";
import { LoadedResult } from "./useLoadedSearch";

interface useTypedLoadedItemProps {
    id?: string;
    subtype?: ItemSubType;
    enabled?: boolean;
    queryKeyPrefix?: string;
}

export interface useTypedLoadedItemResponse
    extends LoadedEntity<GenericFetchResponse> {
    item?: ItemBase;
    // Also expose refetch as some logic requires it
    refetch: () => void;
}
export const useTypedLoadedItem = (
    props: useTypedLoadedItemProps
): useTypedLoadedItemResponse => {
    /**
    Hook: useTypedLoadedItem

    Manages the loading and fetching of a typed registry item. 
    */

    // Timeout cache after 30s
    const cacheTimeoutMs = 30000;
    const enabled = !!props.id && !!props.subtype && (props.enabled ?? true);
    const fetchQuery = useQuery({
        queryKey: [
            (props.queryKeyPrefix ?? "") +
                "typed query" +
                (props.id ?? "") +
                (props.subtype ?? ""),
        ],
        queryFn: () => {
            if (props.id === undefined || props.subtype === undefined) {
                return Promise.reject(
                    "Trying to fetch item by subtype with undefined ID or subtype."
                );
            } else {
                return fetchBySubtype(props.id, props.subtype);
            }
        },
        staleTime: cacheTimeoutMs,
        enabled: enabled,
    });

    return {
        item: fetchQuery.data?.item as ItemBase,
        data: fetchQuery.data,
        refetch: fetchQuery.refetch,
        ...mapQueryToLoadedEntity(fetchQuery),
    };
};

interface useUntypedLoadedItemProps {
    id?: string;
    enabled?: boolean;
    queryKeyPrefix?: string;
}

export const useUntypedLoadedItem = (
    props: useUntypedLoadedItemProps
): LoadedEntity<ItemBase> => {
    /**
    Hook: useUntypedLoadedItem

    Manages the loading and fetching of an untyped registry item. 
    */

    // Timeout cache after 10s
    const cacheTimeoutMs = 10000;
    // Can be disabled by undefined handle or props specifying
    const enabled = props.id !== undefined && (props.enabled ?? true);
    const fetchQuery = useQuery({
        queryKey: [(props.queryKeyPrefix ?? "") + "untyped", props.id],
        queryFn: () => {
            if (props.id === undefined) {
                console.log("Trying to fetch an undefined handle ID!");
                return Promise.reject("Handle could not be parsed from URL");
            } else {
                return fetchRegistryItem(props.id);
            }
        },
        staleTime: cacheTimeoutMs,
        enabled: enabled,
    });

    return {
        data: fetchQuery.data?.item as unknown as ItemBase,
        ...mapQueryToLoadedEntity(fetchQuery),
    };
};

export interface UseCombinedLoadedItemProps {
    id?: string;
    disabled?: boolean;
}
export interface UseCombinedLoadedItemOutput extends LoadedEntity<ItemBase> {}

export const useCombinedLoadedItem = (
    props: UseCombinedLoadedItemProps
): UseCombinedLoadedItemOutput => {
    /**
    Hook: useCombinedLoadedItem

    Manages the loading of an item - fetches typed and untyped variants.

    */
    // Are we allowed to proceed?
    const enabled =
        props.id !== undefined && props.disabled !== undefined
            ? !props.disabled
            : true;

    // Differentiates cache and load state to stop unwanted loading states in
    // main view
    const queryKeyPrefix = "graph-detailed";

    // Load untyped
    const untypedLoad = useUntypedLoadedItem({
        id: props.id,
        enabled: enabled,
        queryKeyPrefix: queryKeyPrefix,
    });

    // Load typed
    const typedLoad = useTypedLoadedItem({
        id: props.id,
        subtype: untypedLoad.data?.item_subtype,
        enabled: enabled,
        queryKeyPrefix: queryKeyPrefix,
    });

    // States

    // This combines the untyped and type load states
    const combinedState = combineLoadStates([typedLoad, untypedLoad]);

    // Display
    return {
        // The response/load status
        ...combinedState,
        data: typedLoad.item,
    };
};
export interface useLoadedSubtypesProps {
    ids: string[];
    subtype: ItemSubType;
}

export type ResultType = LoadedEntity<ItemBase | undefined>;
export type ResultMap = Map<string, ResultType>;

export interface useLoadedSubtypesResponse {
    results: ResultMap;
}
export const useLoadedSubtypes = (
    props: useLoadedSubtypesProps
): useLoadedSubtypesResponse => {
    /**
    Hook: useLoadedSubtypes

    Loads the ID based on the specified subtype - performs a registry typed fetch
    */

    const cacheTimeoutMs = 30000;
    const loadedItems = useQueries({
        queries: props.ids.map((id: string) => {
            return {
                // this matches the main subtype load id so may be cached
                queryKey: [id, props.subtype ?? "no subtype"],
                queryFn: () => {
                    if (props.subtype === undefined) {
                        console.log("Fetching before ready - doing nothing.");
                    } else {
                        return fetchBySubtype(id, props.subtype);
                    }
                },
                staleTime: cacheTimeoutMs,
            };
        }),
    });

    const resultList = loadedItems.map((qResult) => {
        return {
            data: qResult.data?.item,
            ...mapQueryToLoadedEntity(qResult),
        } as ResultType;
    });

    const idResultMap: Map<string, ResultType> = new Map([]);
    for (var i = 0; i < props.ids.length; i++) {
        const id = props.ids[i];
        const result = resultList[i];
        idResultMap.set(id, result);
    }

    return { results: idResultMap };
};
