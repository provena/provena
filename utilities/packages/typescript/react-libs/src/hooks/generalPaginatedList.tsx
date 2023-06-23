import { useEffect, useState } from "react";
import { ItemBase } from "../shared-interfaces/RegistryModels";
import { useQuery } from "@tanstack/react-query";
import { generalList } from "../queries/registry";
import { FilterOptions, SortOptions } from "../shared-interfaces/RegistryAPI";

interface usePaginatedRecordListProps<T extends ItemBase = ItemBase> {
    // Defaults to Updated Timestamp Newest First
    sortBy?: SortOptions;
    // Defaults to no filtering
    filterBy?: FilterOptions;
    // Number of records to fetch
    // uses API default by default
    pageSize?: number;
    // Should the first fetch occur without user input?
    // true by default
    fetchOnStart?: boolean;
    // Are fetches enabled - can be disabled manually here for example if auth
    // is insufficient true by default
    enabled?: boolean;
    // Run a function when more results are loaded?
    onMoreLoaded?: (records: T[]) => void;
}
interface usePaginatedRecordListResponse<T extends ItemBase = ItemBase> {
    records: T[] | undefined;
    moreAvailable: boolean;
    loading: boolean;
    error: boolean;
    errorMessage: string | undefined;
    requestMoreRecords: () => void;
    resetList: () => void;
}
export function usePaginatedRecordList<T extends ItemBase = ItemBase>(
    props: usePaginatedRecordListProps
): usePaginatedRecordListResponse {
    /**
    Hook: usePaginatedRecordList

    Custom hook which auto fetches a record list from the registry. 

    This is based on the paginated endpoint. 

    NOTE when the query sorting/filtering changes the record list is cleared.

    Uses react query to manage the fetching/caching of loaded content.
    */

    // Record list
    const [currentRecords, setCurrentRecords] = useState<T[] | undefined>(
        undefined
    );

    // The pagination key is an object or undefined
    const [lastPaginationKey, setLastPaginationKey] = useState<{} | undefined>(
        undefined
    );

    // Is it the first query?
    var fetchOnStart = true;
    if (props.fetchOnStart !== undefined) {
        if (!props.fetchOnStart) {
            fetchOnStart = false;
        }
    }

    const [firstFetch, setFirstFetch] = useState<boolean>(fetchOnStart);

    // More requested
    const [moreRequested, setMoreRequested] = useState<boolean>(false);

    // More remaining
    const [moreRemaining, setMoreRemaining] = useState<boolean>(true);

    const resetState = () => {
        setCurrentRecords(undefined);
        setLastPaginationKey(undefined);
        // Is it the first query?
        var fetchOnStart = true;
        if (props.fetchOnStart !== undefined) {
            if (!props.fetchOnStart) {
                fetchOnStart = false;
            }
        }
        setFirstFetch(fetchOnStart);
        setMoreRequested(false);
        setMoreRemaining(true);
    };

    // If the sort/filter options change we need to reset the state so that we
    // don't mix multiple result lists
    useEffect(() => {
        resetState();
    }, [
        props.sortBy?.sort_type,
        props.sortBy?.ascending,
        props.filterBy?.item_subtype,
    ]);

    // This accepts additional records into the record list
    const moreItemsHandler = (items: T[]): T[] => {
        const listCopy: T[] = JSON.parse(JSON.stringify(currentRecords ?? []));
        items.forEach((i: T) => {
            listCopy.push(i);
        });
        setCurrentRecords(listCopy);
        return listCopy;
    };

    // A unique key for each paginated request - this includes a combination of filter/sort options + pagination key
    const listQueryKey =
        "paginatedList" +
        JSON.stringify({
            sort: props.sortBy ?? "",
            filter: props.filterBy ?? "",
        }) +
        (lastPaginationKey ? JSON.stringify(lastPaginationKey) : "first");

    // Timeout responses from the paginated list query every 30 seconds
    // const listCacheTimeout = 30000;

    // Should a query be run?
    const userEnabled = props.enabled !== undefined ? props.enabled : true;
    const queryReady =
        userEnabled && (firstFetch || (moreRequested && moreRemaining));

    // Query to list paginated
    const {
        isFetching: paginatedListFetching,
        isError: paginatedListIsError,
        error: paginatedListError,
    } = useQuery({
        queryKey: [listQueryKey],
        queryFn: () => {
            return generalList({
                sort_by: props.sortBy,
                filter_by: props.filterBy,
                pagination_key: lastPaginationKey,
                page_size: props.pageSize,
            });
        },
        // Disable caching for now
        // staleTime: listCacheTimeout,
        // Run a query if first query or more requested
        enabled: queryReady,
        onSuccess(data) {
            // When we get more data successfully we need to:

            // a) mark not first query
            setFirstFetch(false);

            // Detect before modifying more requested whether this was an
            // additional page load
            const moreLoaded = moreRequested;

            // b) set more requested to false
            setMoreRequested(false);

            // c) add the retrieved items to the current item list
            const newRecords = moreItemsHandler((data.items ?? []) as T[]);

            // d) check if there are more items and record pagination key
            if (!!data.pagination_key) {
                setLastPaginationKey(data.pagination_key);
                setMoreRemaining(true);
            } else {
                setLastPaginationKey(undefined);
                setMoreRemaining(false);
            }

            // e) if the user requested an action - perform it
            if (props.onMoreLoaded !== undefined && moreLoaded) {
                props.onMoreLoaded(newRecords);
            }
        },
    });

    // Handler for requesting additional records
    const requestMoreRecords = (): void => {
        if (moreRemaining) {
            setMoreRequested(true);
        } else {
            // Can't request more records where none are available
            console.log(
                "Error: tried to request more records when none are available."
            );
        }
    };

    return {
        records: currentRecords,
        moreAvailable: moreRemaining,
        requestMoreRecords: requestMoreRecords,
        loading: paginatedListFetching,
        error: paginatedListIsError,
        errorMessage: paginatedListError as string | undefined,
        resetList: resetState,
    };
}
