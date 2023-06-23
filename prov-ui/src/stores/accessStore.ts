import { action, makeAutoObservable } from "mobx";
import { AUTH_API_ENDPOINTS, requests } from "react-libs";
import {
    AccessLevel,
    AccessReport,
    AccessReportResponse,
    ComponentName,
} from "../shared-interfaces/AuthAPI";

export class AccessStore {
    // Is the store loading access?
    loading: boolean = false;

    // The results
    registryReadAccess: boolean | undefined = undefined;
    registryWriteAccess: boolean | undefined = undefined;
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
        this.registryReadAccess = undefined;
        this.registryWriteAccess = undefined;
        this.errorMessage = undefined;
        this.forceErrorBypass = false;

        // this is the access report endpoint
        const endpoint = AUTH_API_ENDPOINTS.GENERATE_ACCESS_REPORT;
        requests
            .get(endpoint, {})
            .then(
                action((response) => {
                    let res: AccessReportResponse =
                        response as AccessReportResponse;
                    if (res.status.success) {
                        this.accessReport = res.report;
                        const registryComponentName: ComponentName =
                            "entity-registry";
                        const readLevel: AccessLevel = "READ";
                        const writeLevel: AccessLevel = "WRITE";
                        var registryReadFound = false;
                        var registryWriteFound = false;
                        var registryCompFound = false;
                        for (const component of res.report.components) {
                            if (
                                component.component_name ==
                                registryComponentName
                            ) {
                                // we found the component
                                registryCompFound = true;
                                // this is the provenance store
                                for (const accessRole of component.component_roles) {
                                    // Loop through access roles looking for
                                    // read or write level
                                    if (accessRole.role_level === readLevel) {
                                        registryReadFound = true;
                                        this.registryReadAccess =
                                            accessRole.access_granted;
                                    }
                                    if (accessRole.role_level === writeLevel) {
                                        registryWriteFound = true;
                                        this.registryWriteAccess =
                                            accessRole.access_granted;
                                    }
                                }
                            }
                        }
                        if (
                            !registryCompFound ||
                            !registryReadFound ||
                            !registryWriteFound
                        ) {
                            this.error = true;
                            this.errorMessage =
                                "Failed to find required registry store access roles in the access report.";
                            this.loading = false;
                            this.registryReadAccess = undefined;
                            this.registryWriteAccess = undefined;
                        } else {
                            // Everything went well
                            this.loading = false;
                        }
                    }
                })
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
