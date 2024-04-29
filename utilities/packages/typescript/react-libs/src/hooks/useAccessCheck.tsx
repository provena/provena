import { useQuery } from "@tanstack/react-query";
import {
  LoadedEntity,
  mapQueryToLoadedEntity,
} from "../interfaces/hookInterfaces";
import {
  AccessLevel,
  AccessReport,
  AccessReportResponse,
  ComponentName,
} from "../provena-interfaces/AuthAPI";
import { getAccessReport } from "../queries/auth";
import { useKeycloak } from "@react-keycloak/web";

interface ParseResponse {
  error: boolean;
  errorMessage?: string;
  granted: boolean;
}
const parseReport = (
  report: AccessReport,
  componentName: string,
  desiredAccessLevel: AccessLevel,
): ParseResponse => {
  var desiredFound = false;
  var compFound = false;
  console.log("Report", report);
  for (const component of report.components) {
    if (component.component_name === componentName) {
      // we found the component
      compFound = true;
      // this is the entity registry
      for (const accessRole of component.component_roles) {
        // Loop through access roles looking for
        // read or write level
        // Role must also be granted
        if (
          accessRole.role_level === desiredAccessLevel &&
          accessRole.access_granted
        ) {
          desiredFound = true;
          break;
        }
      }
      if (compFound) {
        break;
      }
    }
  }
  return {
    error: !compFound,
    errorMessage: compFound
      ? undefined
      : "Failed to find desired authorisation component.",
    granted: desiredFound,
  };
};

export interface UseAccessCheckProps {
  componentName: ComponentName;
  desiredAccessLevel: AccessLevel;
}
export interface UseAccessCheckOutput
  extends LoadedEntity<AccessReportResponse> {
  // This granted reflects if fully loaded and successfully parsed
  granted?: boolean;
  // This granted is always present and defaults to false
  fallbackGranted: boolean;
}
export const useAccessCheck = (
  props: UseAccessCheckProps,
): UseAccessCheckOutput => {
  /**
    Hook: useAccessHook

    Manages requests to the access report endpoint to ensure the user has
    appropriate access. Also fronts the keycloak instance so that there is no
    need to use the keycloak shared store.
    */
  const { keycloak } = useKeycloak();
  const keycloakReady = keycloak.authenticated ?? false;

  // Create a query to hit the access api

  // Cache time (1 minute)
  const cacheDuration = 60000;
  const reportQuery = useQuery({
    queryKey: ["getreport"],
    queryFn: getAccessReport,
    staleTime: cacheDuration,
    // Only fetch when keycloak is authenticated
    enabled: keycloakReady,
  });

  // Parse the report if loaded
  const parsedReport = reportQuery.data
    ? parseReport(
        reportQuery.data.report,
        props.componentName,
        props.desiredAccessLevel,
      )
    : undefined;

  return {
    // Return granted if report is loaded and parsed
    granted: parsedReport?.granted,
    // Fallback granted is false if granted is undefined (loading or error)
    fallbackGranted: !!parsedReport?.granted,
    ...mapQueryToLoadedEntity(reportQuery),
  };
};
