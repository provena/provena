import { requests, AUTH_API_ENDPOINTS } from "react-libs";
import { RequestStatus } from "../provena-interfaces/AuthAPI";
export const AdminAccessManagement = {
  getRequests: () => requests.get(AUTH_API_ENDPOINTS.ADMIN_USER_REQUESTS),
  deleteRequest: (username: string, request_id: number) => {
    const body = {
      username: username,
      request_id: request_id,
    };
    return requests.post(AUTH_API_ENDPOINTS.ADMIN_DELETE_REQUEST, body);
  },
  changeRequestState: (
    username: string,
    request_id: number,
    desired_status: RequestStatus,
    send_email_alert: boolean,
  ) => {
    const params = {
      // Include the alert email boolean flag
      send_email_alert: send_email_alert,
    };
    const body = {
      username: username,
      request_id: request_id,
      desired_state: desired_status,
    };
    return requests.post(AUTH_API_ENDPOINTS.ADMIN_STATUS_CHANGE, body, params);
  },
  addNote: (username: string, request_id: number, note: string) => {
    const body = {
      username: username,
      request_id: request_id,
      note: note,
    };
    return requests.post(AUTH_API_ENDPOINTS.ADD_NOTE, body);
  },
};
