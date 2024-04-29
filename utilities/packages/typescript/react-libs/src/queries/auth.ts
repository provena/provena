import { AUTH_API_ENDPOINTS } from "./endpoints";
import {
  AccessReportResponse,
  RequestStatus,
  UserLinkUserAssignRequest,
  UserLinkUserAssignResponse,
  UserLinkUserLookupResponse,
  UserLinkUserValidateRequest,
  UserLinkUserValidateResponse,
} from "../provena-interfaces/AuthAPI";
import { requests } from "../stores";
import { requestErrToMsg } from "../util/util";

export const getAccessReport = () => {
  const endpoint = AUTH_API_ENDPOINTS.GENERATE_ACCESS_REPORT;
  return requests
    .get(endpoint, {})
    .then((res) => {
      const resJson = res as AccessReportResponse;
      try {
        if (!resJson.status.success) {
          return Promise.reject(res);
        } else {
          return resJson;
        }
      } catch (e) {
        return Promise.reject(res);
      }
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

export const getUsernamePersonLink = (inputs: { username?: string }) => {
  const endpoint = AUTH_API_ENDPOINTS.USER_LINK_LOOKUP;

  // Conditionally include the username query string arg to lookup other user's
  // link
  var params: { [k: string]: string } = {};
  if (!!inputs.username) {
    params["username"] = inputs.username;
  }

  return requests
    .get(endpoint, params)
    .then((res) => {
      return res as UserLinkUserLookupResponse;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

interface ValidatePersonLinkInterface {
  personId: string;
}
export const validatePersonLink = (inputs: ValidatePersonLinkInterface) => {
  const endpoint = AUTH_API_ENDPOINTS.USER_LINK_VALIDATE;
  const payload: UserLinkUserValidateRequest = { person_id: inputs.personId };
  return requests
    .post(endpoint, payload)
    .then((res) => {
      return res as UserLinkUserValidateResponse;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

interface AssignPersonLinkInterface {
  personId: string;
}
export const assignPersonLink = (inputs: AssignPersonLinkInterface) => {
  const endpoint = AUTH_API_ENDPOINTS.USER_LINK_ASSIGN;
  const payload: UserLinkUserAssignRequest = { person_id: inputs.personId };
  return requests
    .post(endpoint, payload)
    .then((res) => {
      return res as UserLinkUserAssignResponse;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};
