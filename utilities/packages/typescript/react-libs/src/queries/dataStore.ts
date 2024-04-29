import {
  PresignedURLResponse,
  RegistryFetchResponse,
  ReleaseApprovalRequestResponse,
} from "../provena-interfaces/DataStoreAPI";
import { requests } from "../stores/apiagent";
import { requestErrToMsg } from "../util/util";
import { DATA_STORE_API_ENDPOINTS } from "./endpoints";

export const fetchDataset = (
  handle: string,
): Promise<RegistryFetchResponse> => {
  const endpoint = DATA_STORE_API_ENDPOINTS.FETCH_DATASET;
  const params = {
    handle_id: handle,
  };
  return requests
    .get(endpoint, params)
    .then((res) => {
      const resJson = res as RegistryFetchResponse;
      if (!resJson.status.success || resJson.item === undefined) {
        return Promise.reject(res);
      } else {
        return resJson;
      }
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

export const fetchApproversList = (): Promise<Array<string>> => {
  const endpoint = DATA_STORE_API_ENDPOINTS.FETCH_APPROVERS_LIST;
  return requests
    .get(endpoint)
    .then((res) => {
      const resJson = res as Array<string>;
      return resJson;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

interface ApprovalRequestProps {
  datasetId: string;
  approverId: string;
  requesterNotes: string;
}

export const approvalRequest = (props: ApprovalRequestProps) => {
  const endpoint = DATA_STORE_API_ENDPOINTS.APPROVAL_REQUEST;
  return requests
    .post(
      endpoint,
      {
        dataset_id: props.datasetId,
        approver_id: props.approverId,
        notes: props.requesterNotes,
      },
      {},
    )
    .then((res) => {
      const resJson = res as ReleaseApprovalRequestResponse;
      return resJson;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

interface ApproverActionProps {
  datasetId: string;
  approve: boolean;
  approverNote: string;
}

export const approvalAction = (props: ApproverActionProps) => {
  const endpoint = DATA_STORE_API_ENDPOINTS.APPROVAL_ACTION;
  return requests
    .put(
      endpoint,
      {
        dataset_id: props.datasetId,
        approve: props.approve,
        notes: props.approverNote,
      },
      {},
    )
    .then((res) => {
      const resJson = res as ReleaseApprovalRequestResponse;
      return resJson;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};

export interface GetPresignedUrlInputs {
  path: string;
  datasetId: string;
}

export const getPresignedUrl = (props: GetPresignedUrlInputs) => {
  const endpoint = DATA_STORE_API_ENDPOINTS.SIGN_DATASET;
  return requests
    .post(endpoint, {
      dataset_id: props.datasetId,
      file_path: props.path,
    })
    .then((res) => {
      const resJson = res as PresignedURLResponse;
      return resJson;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};
