import { useQuery } from "@tanstack/react-query";
import { getUsernamePersonLink } from "../queries/auth";
import {
    LoadedWithRefetch,
    mapQueryToLoadedWithRefetch,
} from "../interfaces/hookInterfaces";
import { useAccessCheck } from "./useAccessCheck";
import { useKeycloak } from "@react-keycloak/web";

export interface UseUserLinkServiceLookupProps {
    username?: string;
}
export interface UseUserLinkServiceLookupOutput
    extends LoadedWithRefetch<string | undefined> {
    shouldLink: boolean | undefined;
}
export const useUserLinkServiceLookup = (
    props: UseUserLinkServiceLookupProps
): UseUserLinkServiceLookupOutput => {
    /**
    Hook: useUserLinkServiceLookup
    
    Manages the fetching of the current user link status
    */

    const { keycloak } = useKeycloak();

    // Needs keycloak to be setup before fetching - no other special permissions required
    const enabled = keycloak.authenticated;

    // Cache config (60s)
    const cacheTimeout = 60000;

    // Query to fetch user identity
    const response = useQuery({
        queryKey: [
            "userlinklookup",
            props.username ??
                keycloak.tokenParsed?.username ??
                "unknownusername",
        ],
        queryFn: () => {
            return getUsernamePersonLink({ username: props.username });
        },
        staleTime: cacheTimeout,
        enabled,
    });

    // Check if the user should be linked by checking auth roles
    const writeCheck = useAccessCheck({
        componentName: "entity-registry",
        desiredAccessLevel: "WRITE",
    });

    const personId = response.data?.person_id;
    const regWrite = writeCheck.granted;
    const linked = !!personId;
    const conditionsMet =
        !linked &&
        ((!response.isFetching && !response.error) || undefined) &&
        enabled &&
        regWrite;

    return {
        data: personId,
        shouldLink: conditionsMet,
        ...mapQueryToLoadedWithRefetch(response),
    };
};
