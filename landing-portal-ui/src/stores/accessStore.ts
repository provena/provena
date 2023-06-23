import deepEqual from "deep-equal";
import { makeAutoObservable } from "mobx";
import { AUTH_API_ENDPOINTS, requests } from "react-libs";
import {
    AccessReport,
    AccessReportResponse,
    AccessRequestList,
    AccessRequestResponse,
    ReportAuthorisationComponent,
    ReportComponentRole,
    RequestAccessTableItem,
} from "../shared-interfaces/AuthAPI";

const copyAccessReport = (report: AccessReport) => {
    /**
     * Given an access report, will perform a full deep
     * copy to enable comparison between distinct copies
     * of the old/modified report.
     */
    const compList: Array<ReportAuthorisationComponent> = [];

    for (var comp of report.components) {
        const roleList: Array<ReportComponentRole> = [];
        for (var role of comp.component_roles) {
            roleList.push({ ...role });
        }
        compList.push({
            component_name: comp.component_name,
            component_roles: roleList,
        });
    }
    const response: AccessReport = {
        components: compList,
    };

    return response;
};

export class AccessStore {
    proposedAccessReport: AccessReport | undefined;
    currentAccessReport: AccessReport | undefined;
    successfulReportMade: boolean = false;
    accessRoleIsEmpty: boolean = false;
    accessRolesUpdating: boolean = false;
    accessRolesRequesting: boolean = false;
    accessRolesRequestingDialog: boolean = false;
    adminAccess: boolean = false;
    accessCheckMsg: string | undefined;
    accessRequestedItems: Array<RequestAccessTableItem> | undefined;
    successfulResponseMessage: string =
        "Your request has been sent to an admin. You will be notified via email when your request is handled. The status of your request is visible in the list of active requests below. Please make another request if you don't hear anything within 5 business days.";
    accessRequestResponseMessage: string | undefined = undefined;

    constructor() {
        makeAutoObservable(this);
    }

    rolesChanged() {
        /**
         * Returns whether the access roles have been changed due
         * to users toggling the access request switches. Uses a
         * JSON stringify to perform a deep copy.
         */
        return !deepEqual(this.proposedAccessReport, this.currentAccessReport);
    }

    generateAccessReport() {
        requests.get(AUTH_API_ENDPOINTS.GENERATE_ACCESS_REPORT).then((res) => {
            const returnedReport = res as AccessReportResponse;
            if (returnedReport.status.success) {
                // Be careful to deep copy
                this.proposedAccessReport = copyAccessReport(
                    returnedReport.report
                );
                this.currentAccessReport = copyAccessReport(
                    returnedReport.report
                );
            }
            this.checkNoneRoles(this.currentAccessReport!);
            this.checkAdminAccess(this.currentAccessReport!);
        });
    }

    checkAdminAccess(roles: AccessReport) {
        for (const component of roles.components) {
            if (component.component_name == "sys-admin") {
                for (const access of component.component_roles) {
                    if (access.access_granted) {
                        this.adminAccess = true;
                        return;
                    }
                }
            }
        }
        this.adminAccess = false;
    }

    testAccess() {
        this.successfulReportMade = false;
        this.generateAccessReport();
        this.getFullUserRequestHistory();
    }

    checkNoneRoles(roles: AccessReport) {
        let noneRoles = true;
        for (const component of roles.components) {
            for (const ac of component.component_roles) {
                if (ac.access_granted === true) noneRoles = false;
            }
        }
        console.log("noneRoles", noneRoles);
        this.accessRoleIsEmpty = noneRoles;
    }

    closeFirstTimeLoginAlert() {
        this.accessRoleIsEmpty = false;
    }

    updateRoles(roleName: string, new_access_granted: boolean) {
        //True means leave, false means join
        console.log("update role: ", roleName, new_access_granted);
        for (let group of this.proposedAccessReport!.components) {
            for (let role of group.component_roles) {
                if (role.role_name === roleName) {
                    role.access_granted = new_access_granted;
                }
            }
        }
        // Reset the successful report made display
        this.successfulReportMade = false;
    }
    requestRolesUpdate() {
        this.accessRolesRequesting = true;
        requests
            .post(
                AUTH_API_ENDPOINTS.REQUEST_ACCESS_CHANGE,
                this.proposedAccessReport
            )
            .then((response) => {
                let res = response as AccessRequestResponse;
                this.accessRolesUpdating = false;
                if (res.status.success) {
                    this.accessRolesRequestingDialog = true;
                    this.accessRequestResponseMessage =
                        this.successfulResponseMessage;
                    this.currentAccessReport = copyAccessReport(
                        this.proposedAccessReport!
                    );
                    this.successfulReportMade = true;
                } else {
                    this.accessRequestResponseMessage =
                        res.status.details ??
                        "Something went wrong when making your request. Undefined error.";
                    this.accessRolesRequestingDialog = true;
                }
                this.getFullUserRequestHistory();
            })
            .finally(() => {
                this.accessRolesRequesting = false;
            });
    }
    closeDialog() {
        this.accessRolesRequestingDialog = false;
    }

    getFullUserRequestHistory() {
        requests
            .get(AUTH_API_ENDPOINTS.GET_FULL_USER_REQUEST_HISTORY)
            .then((response) => {
                let res = response as AccessRequestList;
                this.accessRequestedItems = res.items;
            });
    }
}

export default new AccessStore();
