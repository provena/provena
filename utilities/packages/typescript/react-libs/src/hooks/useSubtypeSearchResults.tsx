import { ItemSubType } from "../provena-interfaces/RegistryAPI";
import { useQuery } from "@tanstack/react-query";
import { searchRegistry } from "../queries/search";
import { QueryResult } from "../provena-interfaces/SearchAPI";
import { LoadedEntity, mapQueryToLoadedEntity } from "../interfaces";

interface useSearchResultsProps {
  // What subtype?
  subtype?: ItemSubType;
  // What is the query?
  searchQuery?: string;
  // How many results should be loaded from search?
  // DEFAULT = 10
  searchLimit?: number;
  // Enabled?
  enabled?: boolean;
}
interface useSearchResultsResponse extends LoadedEntity<QueryResult[]> {}

export const useSearchResults = (
  props: useSearchResultsProps,
): useSearchResultsResponse => {
  /**
    Hook: useSubtypeSearchResults

    A custom hook which manages searching. 

    The input should be debounced.
    */

  // cache timeout 10 seconds
  const searchCacheTimeout = 10000;

  // This should force a requery if the search query or subtype changes
  const queryKey =
    (props.searchQuery ?? "no-search-query") + (props.subtype ?? "no-subtype");

  const searchQuery = useQuery({
    queryKey: [queryKey],
    queryFn: () => {
      // search including optional result limit count and subtype
      return searchRegistry(props.searchQuery ?? "", props.searchLimit, props.subtype);
    },
    enabled: (props.enabled ?? true) && props.searchQuery !== undefined,
    staleTime: searchCacheTimeout,
  });

  return {
    data: searchQuery.data?.results,
    ...mapQueryToLoadedEntity(searchQuery),
  };
};
