import { useQueries } from "@tanstack/react-query";
import debounce from "lodash.debounce";
import { useCallback, useEffect, useState } from "react";
import { LoadedEntity } from "../interfaces";
import { generalFetch } from "../queries";
import { ItemBase, ItemSubType } from "../provena-interfaces/RegistryModels";
import { QueryResult } from "../provena-interfaces/SearchAPI";
import { useSearchResults } from "./useSubtypeSearchResults";

export interface LoadedResult {
  id: string;
  item?: ItemBase;
  loading: boolean;
  isError: boolean;
  errorMessage?: string;
}

export interface useLoadedSearchProps {
  // Query
  searchQuery?: string;
  // Filter by subtype?
  subtype?: ItemSubType;


  // How many results should be loaded from search?
  // DEFAULT = 10
  searchLimit?: number;

  // Enabled?
  enabled?: boolean;
}
interface useLoadedSearchResponse extends LoadedEntity<LoadedResult[]> {}
export const useLoadedSearch = (
  props: useLoadedSearchProps,
): useLoadedSearchResponse => {
  /**
    Hook: useLoadedSubtypeSearch

    Manages a list of loaded/loading resources as per search query results.

    The input is internally debounced.
    */

  // Store an internal debounced version of input search query
  const [internalDebounceQuery, setInternalDebounceQuery] = useState<
    string | undefined
  >(props.searchQuery);

  // Update the internal search query in a debounced way
  const debounceMs = 500;
  // Need to use a call back so this function is persisted between renders
  const debouncedSetSearchQuery = useCallback(
    debounce(setInternalDebounceQuery, debounceMs),
    [],
  );

  useEffect(() => {
    debouncedSetSearchQuery(props.searchQuery);
  }, [props.searchQuery]);

  // Manage an unloaded list of search results - this is debounced
  const searchQuery = useSearchResults({
    searchQuery: internalDebounceQuery,
    enabled: props.enabled ?? true,
    subtype: props.subtype,
    searchLimit: props.searchLimit
  });

  // Manage a corresponding list of fetches for each result
  const cacheTimeoutMs = 30000;
  const loadedResults = useQueries({
    queries: (searchQuery.data ?? []).map((q: QueryResult) => {
      return {
        queryKey: [q.id],
        queryFn: () => {
          return generalFetch(q.id);
        },
        staleTime: cacheTimeoutMs,
        enabled: props.enabled ?? true,
      };
    }),
  });

  // Derive the loaded results in the desired format
  const loadedParsedResults: LoadedResult[] | undefined =
    searchQuery.data &&
    loadedResults.map((query, index) => {
      const resultItem = searchQuery.data![index];
      const { isFetching, data, isError, error } = query;
      return {
        id: resultItem.id,
        item: data?.item as unknown as ItemBase,
        loading: isFetching,
        isError: isError,
        errorMessage: error as string | undefined,
      };
    });

  return {
    ...searchQuery,
    data: loadedParsedResults,
  };
};
