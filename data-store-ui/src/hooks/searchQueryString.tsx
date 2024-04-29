import { useQueryStringVariable } from "react-libs";

export const SEARCH_QUERY_STRING_KEY: string = "searchquery";

interface useSearchQueryStringProps {}
interface useSearchQueryStringResponse {
  searchQuery: string;
  setSearchQuery: (searchQuery: string) => void;
}
export const useSearchQueryString = (
  props: useSearchQueryStringProps,
): useSearchQueryStringResponse => {
  /**
    Hook: useSearchQueryString
    
    */
  const { value: searchQuery, setValue: setSearchQuery } =
    useQueryStringVariable({ queryStringKey: SEARCH_QUERY_STRING_KEY });

  return {
    searchQuery: searchQuery ?? "",
    setSearchQuery: (query: string) => {
      if (setSearchQuery !== undefined) {
        setSearchQuery(query);
      }
    },
  };
};
