import { action, makeAutoObservable } from "mobx";
import { AUTH_API_ENDPOINTS, requests } from "react-libs";
import {
  ListGroupsResponse,
  ListUserMembershipResponse,
  UserGroupMetadata,
} from "../provena-interfaces/AuthAPI";

export class GroupStore {
  loadingGroups: boolean = false;
  errorLoadingGroups: boolean = false;
  errorLoadingGroupsMessage: string | undefined = undefined;
  groups: Array<UserGroupMetadata> | undefined = undefined;

  loadingUserGroups: boolean = false;
  errorLoadingUserGroups: boolean = false;
  errorLoadingUserGroupsMessage: string | undefined = undefined;
  userGroups: Array<UserGroupMetadata> | undefined = undefined;

  constructor() {
    makeAutoObservable(this);
  }

  fetchGroups() {
    // Reset group fetch
    this.loadingGroups = true;
    this.errorLoadingGroups = false;
    this.errorLoadingGroupsMessage = undefined;

    requests
      .get(AUTH_API_ENDPOINTS.LIST_GROUPS, {})
      .then((res) => {
        const response: ListGroupsResponse = res as ListGroupsResponse;
        if (response.status.success) {
          if (response.groups) {
            this.groups = response.groups;
          } else {
            this.errorLoadingGroups = true;
            this.errorLoadingGroupsMessage =
              "Groups could not be listed. Contact admin.";
          }
        } else {
          this.errorLoadingGroups = true;
          this.errorLoadingGroupsMessage =
            "Groups could not be listed. Contact admin. Details: " +
            response.status.details;
        }
      })
      .catch(
        action((e: any) => {
          this.errorLoadingGroups = true;
          if (e.response) {
            this.errorLoadingGroupsMessage = `Failed to load groups. Response status code: ${
              e.response.status
            } and error detail: ${e.response.data.detail ?? "Unknown"}`;
          } else if (e.message) {
            this.errorLoadingGroupsMessage = `Failed to load groups. Response message: ${e.message}.`;
          } else {
            this.errorLoadingGroupsMessage =
              "Failed to load groups! Unknown error occurred.";
          }
        }),
      )
      .finally(() => {
        this.loadingGroups = false;
      });
  }

  populateUserGroups() {
    // Reset user fetch
    this.loadingUserGroups = true;
    this.errorLoadingUserGroups = false;
    this.errorLoadingUserGroupsMessage = undefined;

    requests
      .get(AUTH_API_ENDPOINTS.LIST_USER_MEMBERSHIP, {})
      .then((res) => {
        const response: ListUserMembershipResponse =
          res as ListUserMembershipResponse;
        if (response.status.success) {
          if (response.groups) {
            this.userGroups = response.groups;
          } else {
            this.errorLoadingUserGroups = true;
            this.errorLoadingUserGroupsMessage =
              "User membership could not be listed. Contact admin.";
          }
        } else {
          this.errorLoadingUserGroups = true;
          this.errorLoadingUserGroupsMessage =
            "User membership could not be listed. Contact admin. Details: " +
            response.status.details;
        }
      })
      .catch(
        action((e: any) => {
          this.errorLoadingUserGroups = true;
          if (e.response) {
            this.errorLoadingUserGroupsMessage = `Failed to load user groups. Response status code: ${
              e.response.status
            } and error detail: ${e.response.data.detail ?? "Unknown"}`;
          } else if (e.message) {
            this.errorLoadingUserGroupsMessage = `Failed to load user groups. Response message: ${e.message}.`;
          } else {
            this.errorLoadingUserGroupsMessage =
              "Failed to load user groups! Unknown error occurred.";
          }
        }),
      )
      .finally(() => {
        this.loadingUserGroups = false;
      });
  }

  resetStore() {
    this.loadingGroups = false;
    this.errorLoadingGroups = false;
    this.errorLoadingGroupsMessage = undefined;
    this.groups = undefined;
    this.loadingUserGroups = false;
    this.errorLoadingUserGroups = false;
    this.errorLoadingUserGroupsMessage = undefined;
    this.userGroups = undefined;
  }
}

export default new GroupStore();
