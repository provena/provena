import { ItemSubType } from "../shared-interfaces/RegistryAPI";
import { useQuery } from "@tanstack/react-query";
import { searchRegistry } from "../queries/search";
import { QueryResult } from "../shared-interfaces/SearchAPI";
import { LoadedEntity, mapQueryToLoadedEntity } from "../interfaces";

interface useSearchResultsProps {
    // What subtype?
    subtype?: ItemSubType;
    // What is the query?
    searchQuery?: string;
    // Enabled?
    enabled?: boolean;
}
interface useSearchResultsResponse extends LoadedEntity<QueryResult[]> {}

export const useSearchResults = (
    props: useSearchResultsProps
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
        (props.searchQuery ?? "no-search-query") +
        (props.subtype ?? "no-subtype");

    const searchQuery = useQuery({
        queryKey: [queryKey],
        queryFn: () => {
            return searchRegistry(props.searchQuery ?? "", props.subtype);
        },
        enabled: (props.enabled ?? true) && props.searchQuery !== undefined,
        staleTime: searchCacheTimeout,
    });

    return {
        data: searchQuery.data?.results,
        ...mapQueryToLoadedEntity(searchQuery),
    };
};
