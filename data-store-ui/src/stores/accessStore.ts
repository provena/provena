import { action, makeAutoObservable } from "mobx";
import { AUTH_API_ENDPOINTS, requests } from "react-libs";
import {
  AccessLevel,
  AccessReport,
  AccessReportResponse,
  ComponentName,
} from "../provena-interfaces/AuthAPI";

export class AccessStore {
  // Is the store loading access?
  loading: boolean = false;

  // The results
  readAccess: boolean | undefined = undefined;
  writeAccess: boolean | undefined = undefined;
  accessReport: AccessReport | undefined = undefined;

  // Was there an error?
  error: boolean = false;
  errorMessage: string | undefined = undefined;

  // Dismissing the error dialog allows forced attempt
  // as a worst case attempt to let the user progress
  forceErrorBypass: boolean = false;

  constructor() {
    makeAutoObservable(this);
  }

  dismissError() {
    // Dismiss the error dialog
    // leaves in state such that it will
    // show authorisation error
    this.error = false;
    this.errorMessage = undefined;
    this.accessReport = undefined;
    this.loading = false;
    this.forceErrorBypass = true;
  }

  checkAccess() {
    // Reset any pending results
    this.error = false;
    this.loading = true;
    this.accessReport = undefined;
    this.readAccess = undefined;
    this.writeAccess = undefined;
    this.errorMessage = undefined;
    this.forceErrorBypass = false;

    // this is the access report endpoint
    const endpoint = AUTH_API_ENDPOINTS.GENERATE_ACCESS_REPORT;
    requests
      .get(endpoint, {})
      .then(
        action((response) => {
          let res: AccessReportResponse = response as AccessReportResponse;
          if (res.status.success) {
            this.accessReport = res.report;
            const componentName: ComponentName = "entity-registry";
            const readLevel: AccessLevel = "READ";
            const writeLevel: AccessLevel = "WRITE";
            var readFound = false;
            var writeFound = false;
            var compFound = false;
            for (const component of res.report.components) {
              if (component.component_name == componentName) {
                // we found the component
                compFound = true;
                // this is the data-store
                for (const accessRole of component.component_roles) {
                  // Loop through access roles looking for
                  // read or write level
                  if (accessRole.role_level == readLevel) {
                    readFound = true;
                    this.readAccess = accessRole.access_granted;
                  }
                  if (accessRole.role_level == writeLevel) {
                    writeFound = true;
                    this.writeAccess = accessRole.access_granted;
                  }
                }
              }
            }
            if (!compFound || !readFound || !writeFound) {
              this.error = true;
              this.errorMessage =
                "Failed to find required access roles in the access report.";
              this.loading = false;
              this.readAccess = undefined;
              this.writeAccess = undefined;
            } else {
              // Everything went well
              this.loading = false;
            }
          }
        }),
      )
      .catch((e: any) => {
        this.error = true;
        this.loading = false;
        if (e.response) {
          this.errorMessage = `Failed to load access report! Response status code: ${
            e.response.status
          } and error detail: ${e.response.data.detail ?? "Unknown"}`;
        } else if (e.message) {
          this.errorMessage = `Failed to load access report! Response message: ${e.message}.`;
        } else {
          this.errorMessage =
            "Failed to load access report! Unknown error occurred.";
        }
      });
  }
}

export default new AccessStore();
