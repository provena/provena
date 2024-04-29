import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

export type PaginationKey = { [k: string]: any };

interface PaginatedOutput {
  pagination_key?: PaginationKey;
}

interface UseGenericPaginatedListProps<
  // List data type
  ListType,
  // The query result type - must include pagination
  QueryResultType extends PaginatedOutput,
> {
  // The user must provide a function which given a pagination key will fetch more items
  pagerFunction: (
    paginationKey: PaginationKey | undefined,
    limit: number,
  ) => Promise<QueryResultType>;

  // The user must specify how to map from the response object to an array of T
  itemExtractFunction: (loadedItem: QueryResultType) => Array<ListType>;

  // Some unique key for the query
  queryKey: string;

  // Number of records to fetch - default 10
  limit?: number;
  // Should the first fetch occur without user input?
  // true by default
  fetchOnStart?: boolean;
  // Are fetches enabled - can be disabled manually here for example if auth
  // is insufficient true by default
  enabled?: boolean;
  // Run a function when more results are loaded?
  onMoreLoaded?: (records: ListType[]) => void;
}
interface UseGenericPaginatedListOutput<ListType> {
  records: ListType[] | undefined;
  moreAvailable: boolean;
  loading: boolean;
  error: boolean;
  errorMessage: string | undefined;
  requestMoreRecords: () => void;
  resetList: () => void;
}
export function useGenericPaginatedList<
  // List data type
  ListType,
  // The query result type - must include pagination
  QueryResultType extends PaginatedOutput,
>(
  props: UseGenericPaginatedListProps<ListType, QueryResultType>,
): UseGenericPaginatedListOutput<ListType> {
  /**
    Hook: usePaginatedRecordList

    This is a generic version of the registry paginated list endpoint which
    provides a mechanism to decouple the generic loading logic from the specific
    types/queries used.
    */

  // Record list
  const [currentRecords, setCurrentRecords] = useState<ListType[] | undefined>(
    undefined,
  );

  // The pagination key is an object or undefined
  const [lastPaginationKey, setLastPaginationKey] = useState<
    PaginationKey | undefined
  >(undefined);

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

  // This accepts additional records into the record list
  const moreItemsHandler = (items: ListType[]): ListType[] => {
    const listCopy: ListType[] = JSON.parse(
      JSON.stringify(currentRecords ?? []),
    );
    items.forEach((i: ListType) => {
      listCopy.push(i);
    });
    setCurrentRecords(listCopy);
    return listCopy;
  };

  // A unique key for each paginated request - this includes a combination of filter/sort options + pagination key
  const listQueryKey =
    props.queryKey +
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
      return props.pagerFunction(lastPaginationKey, props.limit ?? 10);
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
      const newRecords = moreItemsHandler(props.itemExtractFunction(data));

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
        "Error: tried to request more records when none are available.",
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
