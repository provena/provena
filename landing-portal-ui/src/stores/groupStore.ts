import { action, makeAutoObservable } from "mobx";
import { AUTH_API_ENDPOINTS, requests } from "react-libs";
import {
  AddGroupResponse,
  AddMemberResponse,
  DescribeGroupResponse,
  GroupUser,
  ListGroupsResponse,
  ListMembersResponse,
  ListUserMembershipResponse,
  RemoveGroupResponse,
  RemoveMemberResponse,
  RemoveMembersRequest,
  StatusResponse,
  UpdateGroupResponse,
  UserGroupMetadata,
} from "../provena-interfaces/AuthAPI";

class APIAction<T> {
  // Action status
  loading: boolean = false;
  error: boolean = false;
  succeeded: boolean = false;
  errorMessage: string | undefined = undefined;
  content: T | undefined = undefined;

  // Action promise
  getActionPromise: (
    request: () => Promise<any>,
    markSucceeded: () => void,
    setError: (error: boolean) => void,
    setLoading: (loading: boolean) => void,
    setErrorMessage: (message: string | undefined) => void,
    setContent: (content: T) => void,
  ) => Promise<T>;

  constructor(
    action: (
      request: () => Promise<any>,
      markSucceeded: () => void,
      setError: (error: boolean) => void,
      setLoading: (loading: boolean) => void,
      setErrorMessage: (message: string | undefined) => void,
      setContent: (content: T) => void,
    ) => Promise<T>,
  ) {
    makeAutoObservable(this);
    this.getActionPromise = action;
  }

  // Reset the state
  runAction(request: () => Promise<any>) {
    return this.getActionPromise(
      // request action
      request,
      action(() => {
        this.succeeded = true;
      }),
      action((error: boolean) => {
        this.error = error;
      }),
      action((loading: boolean) => {
        this.loading = loading;
      }),
      action((errorMessage: string | undefined) => {
        this.errorMessage = errorMessage;
      }),
      action((content: T) => {
        this.content = content;
      }),
    );
  }

  awaitingLoad() {
    // we shouldn't be loading, have an error, or have succeeded
    return !this.loading && !this.error && !this.succeeded;
  }

  failed() {
    return this.error;
  }

  ready() {
    // we shouldn't be loading, have an error, success should be marked and
    // content defined
    return (
      !this.loading &&
      !this.error &&
      this.content !== undefined &&
      this.succeeded
    );
  }

  reset() {
    this.loading = false;
    this.error = false;
    this.succeeded = false;
    this.errorMessage = undefined;
    this.content = undefined;
  }
}

function generateLockAction<T extends StatusResponse>(
  actionName: string,
): APIAction<T> {
  return new APIAction<T>(
    (
      request: () => Promise<any>,
      markSucceeded: () => void,
      setError: (error: boolean) => void,
      setLoading: (loading: boolean) => void,
      setErrorMessage: (message: string | undefined) => void,
      setContent: (content: T) => void,
    ) => {
      return new Promise((resolve, reject) => {
        setLoading(true);
        setError(false);
        setErrorMessage(undefined);

        // Run the specified request promise
        request()
          .then((res) => {
            let statusResponse = res as T;
            if (statusResponse.status.success) {
              // set the content
              setContent(statusResponse);
              // mark as success
              markSucceeded();
              // Respond with data
              resolve(statusResponse);
            } else {
              reject(statusResponse.status.details);
            }
          })
          .catch((error) => {
            var errorMessage = "";
            console.log(error);
            var response;
            // Pull out response if present
            if (error.response) {
              response = error.response;
            } else {
              // try using e itself as respone
              response = error;
            }
            // Parse errors
            try {
              errorMessage = `Failed to ${actionName}! Response status code: ${
                response.status
              } and error detail: ${response.data.detail ?? "Unknown"}`;
            } catch (err) {
              if (response.message) {
                errorMessage = `Failed to ${actionName}! Response message: ${response.message}.`;
              } else {
                errorMessage = `Failed to ${actionName}! Unknown error occurred.`;
              }
            }
            setError(true);
            setErrorMessage(errorMessage);
            reject(errorMessage);
          })
          .finally(() => {
            setLoading(false);
          });
      });
    },
  );
}

export class GroupStore {
  // Actions
  listGroupsAction = generateLockAction<ListGroupsResponse>("list groups");
  describeGroupAction =
    generateLockAction<DescribeGroupResponse>("describe group");
  listMembersAction = generateLockAction<ListMembersResponse>("list members");
  listUserMembershipAction = generateLockAction<ListUserMembershipResponse>(
    "list user membership",
  );
  addMemberAction = generateLockAction<AddMemberResponse>(
    "add member to group",
  );
  removeMemberAction = generateLockAction<RemoveMemberResponse>(
    "remove member from group",
  );
  removeMembersAction = generateLockAction<RemoveMemberResponse>(
    "remove members from group",
  );
  addGroupAction = generateLockAction<AddGroupResponse>("create group");
  removeGroupAction = generateLockAction<RemoveGroupResponse>("remove group");
  updateGroupAction = generateLockAction<UpdateGroupResponse>("update group");

  actions: Array<APIAction<any>> = [
    this.listGroupsAction,
    this.describeGroupAction,
    this.listMembersAction,
    this.listUserMembershipAction,
    this.addMemberAction,
    this.removeMemberAction,
    this.removeMembersAction,
    this.addGroupAction,
    this.removeGroupAction,
    this.updateGroupAction,
  ];

  fetchGroupList() {
    return this.listGroupsAction.runAction(() => {
      return requests.get(AUTH_API_ENDPOINTS.ADMIN_LIST_GROUPS);
    });
  }

  describeGroup(groupId: string) {
    return this.describeGroupAction.runAction(() => {
      return requests.get(AUTH_API_ENDPOINTS.ADMIN_DESCRIBE_GROUP, {
        id: groupId,
      });
    });
  }

  listMembers(groupId: string) {
    return this.listMembersAction.runAction(() => {
      return requests.get(AUTH_API_ENDPOINTS.ADMIN_LIST_MEMBERS, {
        id: groupId,
      });
    });
  }

  listUserMembership(userEmail: string) {
    return this.listUserMembershipAction.runAction(() => {
      return requests.get(AUTH_API_ENDPOINTS.ADMIN_LIST_USER_MEMBERSHIP, {
        user_email: userEmail,
      });
    });
  }

  addMember(user: GroupUser, groupId: string) {
    return this.addMemberAction.runAction(() => {
      return requests.post(AUTH_API_ENDPOINTS.ADMIN_ADD_MEMBER, user, {
        group_id: groupId,
      });
    });
  }
  removeMember(email: string, groupId: string) {
    return this.removeMemberAction.runAction(() => {
      return requests.delete(
        AUTH_API_ENDPOINTS.ADMIN_REMOVE_MEMBER,
        {},
        {
          group_id: groupId,
          user_email: email,
        },
      );
    });
  }
  removeMembers(usernames: Array<string>, groupId: string) {
    return this.removeMembersAction.runAction(() => {
      return requests.delete(
        AUTH_API_ENDPOINTS.ADMIN_REMOVE_MEMBERS,
        {
          member_usernames: usernames,
          group_id: groupId,
        } as RemoveMembersRequest,
        {},
      );
    });
  }

  addGroup(metadata: UserGroupMetadata) {
    return this.addGroupAction.runAction(() => {
      return requests.post(AUTH_API_ENDPOINTS.ADMIN_ADD_GROUP, metadata);
    });
  }
  removeGroup(groupId: string) {
    return this.removeGroupAction.runAction(() => {
      return requests.delete(
        AUTH_API_ENDPOINTS.ADMIN_REMOVE_GROUP,
        {},
        {
          id: groupId,
        },
      );
    });
  }
  updateGroup(metadata: UserGroupMetadata) {
    console.log(metadata);
    return this.updateGroupAction.runAction(() => {
      return requests.put(AUTH_API_ENDPOINTS.ADMIN_UPDATE_GROUP, metadata);
    });
  }
  constructor() {
    makeAutoObservable(this);
  }

  resetStore() {
    for (const action of this.actions) {
      action.reset();
    }
  }
}

export default new GroupStore();
