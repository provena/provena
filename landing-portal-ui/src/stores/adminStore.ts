import { makeAutoObservable } from "mobx";
import {
  AccessRequestList,
  RequestAccessTableItem,
  RequestStatus,
  Status,
  ChangeStateStatus,
} from "../provena-interfaces/AuthAPI";
import { AdminAccessManagement } from "../queries/accessManagement";
import { requestErrToMsg } from "react-libs";

export class AdminStore {
  retrievingRequests: boolean = false;
  requests: Array<RequestAccessTableItem> | undefined;
  requestFailure: boolean = false;

  changingState: boolean = false;
  deleting: boolean = false;
  updating_status: boolean = false;
  adding_note: boolean = false;

  constructor() {
    makeAutoObservable(this);
  }

  getAllRequests() {
    this.retrievingRequests = true;
    AdminAccessManagement.getRequests()
      .then((response) => {
        let res = response as AccessRequestList;
        this.requests = res.items;
        this.retrievingRequests = false;
      })
      .catch((err) => {
        this.requestFailure = true;
        console.log(
          "Something went wrong making requests. Error code " +
            err.status +
            " with details: " +
            err.data.detail,
        );
        console.log(err);
        this.retrievingRequests = false;
      });
  }

  deleteRequest(
    username: string,
    request_id: number,
    onCompletion: () => void = () => null,
    onFailure: (reason: string) => void = (reason: string) => null,
  ) {
    this.deleting = true;
    AdminAccessManagement.deleteRequest(username, request_id)
      .then((response) => {
        let res = response as Status;
        if (res["success"]) {
          this.deleting = false;
          onCompletion();
        } else {
          this.deleting = false;
          console.log("Delete failed");
          console.log(res["details"]);
          onFailure(res["details"] ?? "");
        }
      })
      .catch((err) => {
        this.deleting = false;
        console.log("Delete failed");
        console.log(err);
        onFailure(requestErrToMsg(err));
      });
  }

  updateStatus(
    username: string,
    request_id: number,
    send_email_alert: boolean,
    desired_status: RequestStatus,
    onCompletion: () => void = () => null,
    onFailure: (reason: string) => void = (reason: string) => null,
  ) {
    this.updating_status = true;
    AdminAccessManagement.changeRequestState(
      username,
      request_id,
      desired_status,
      send_email_alert,
    )
      .then((response) => {
        let res = response as ChangeStateStatus;
        this.updating_status = false;
        if (!send_email_alert) {
          if (res.state_change.success) {
            onCompletion();
          } else {
            console.log("Status update failed");
            console.log(res.state_change.details ?? "");
            onFailure(res.state_change.details ?? "");
          }
        } else {
          if (res.state_change.success) {
            if (res.state_change.success) {
              // Both successful
              onCompletion();
            } else {
              // Only state change succeeded
              console.log("Status change success, email failure.");
              console.log(res.email_alert.details ?? "");
              onFailure(
                "Status changed successfully, email failure -> " +
                  res.email_alert.details ?? "Unknown",
              );
            }
          } else {
            // State change failed - email definitely failed just show
            // state change failure
            console.log("Status update failed");
            console.log(res.state_change.details);
            onFailure(
              res.state_change.details ??
                "Undefined error" + "... Email not sent.",
            );
          }
        }
      })
      .catch((err) => {
        this.updating_status = false;
        console.log("Status update failed");
        console.log(err);
        onFailure(requestErrToMsg(err));
      });
  }
  addNote(
    username: string,
    request_id: number,
    note: string,
    onCompletion: () => void = () => null,
    onFailure: (reason: string) => void = (reason: string) => null,
  ) {
    this.adding_note = true;
    AdminAccessManagement.addNote(username, request_id, note)
      .then((response) => {
        let res = response as Status;
        if (res.success) {
          this.adding_note = false;
          onCompletion();
        } else {
          this.adding_note = false;
          console.log("Add note failed");
          console.log(res.details);
          onFailure(res.details ?? "Undefined error.");
        }
      })
      .catch((err) => {
        this.adding_note = false;
        console.log("Add note failed");
        console.log(err);
        onFailure(requestErrToMsg(err));
      });
  }
}

export default new AdminStore();
