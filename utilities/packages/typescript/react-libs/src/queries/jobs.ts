import { requests } from "../stores";
import { JOB_API_ENDPOINTS } from "./endpoints";
import {
    AdminLaunchJobRequest,
    AdminLaunchJobResponse,
    GetJobResponse,
    ListByBatchRequest,
    ListByBatchResponse,
    ListJobsRequest,
    ListJobsResponse,
} from "../shared-interfaces/AsyncJobAPI";
import { requestErrToMsg } from "../util/util";
import { PaginationKey } from "../hooks";

interface GetJobBySessionIdInput {
    sessionId: string;
    adminMode: boolean;
}
export function getJobBySessionId(inputs: GetJobBySessionIdInput) {
    /**
    Function: getJobBySessionId
    
    */
    const endpoint = inputs.adminMode
        ? JOB_API_ENDPOINTS.ADMIN_FETCH
        : JOB_API_ENDPOINTS.USER_FETCH;

    return requests
        .get(endpoint, { session_id: inputs.sessionId })
        .then((res) => {
            return res as GetJobResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
}

interface ListJobsInput {
    paginationKey?: PaginationKey;
    limit: number;
    adminMode?: boolean;
}
export function listJobs(inputs: ListJobsInput) {
    /**
    Function: userListJobs
    
    */
    const endpoint = inputs.adminMode
        ? JOB_API_ENDPOINTS.ADMIN_LIST
        : JOB_API_ENDPOINTS.USER_LIST;
    const request = {
        limit: inputs.limit,
        pagination_key: inputs.paginationKey,
    } as ListJobsRequest;

    return requests
        .post(endpoint, request)
        .then((res) => {
            return res as ListJobsResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
}

export const describeBatch = (inputs: {
    batchId: string;
    paginationKey?: PaginationKey;
    limit?: number;
    adminMode?: boolean;
}) => {
    // TODO Handle the pagination properly here and in consuming entities
    const endpoint = inputs.adminMode
        ? JOB_API_ENDPOINTS.ADMIN_LIST_BATCH
        : JOB_API_ENDPOINTS.USER_LIST_BATCH;
    const payload = {
        batch_id: inputs.batchId,
        pagination_key: inputs.paginationKey,
        limit: inputs.limit,
    } as ListByBatchRequest;
    return requests
        .post(endpoint, payload)
        .then((res) => {
            return res as ListByBatchResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const adminLaunchJob = (inputs: { request: AdminLaunchJobRequest }) => {
    const endpoint = JOB_API_ENDPOINTS.ADMIN_LAUNCH_JOB;
    return requests
        .post(endpoint, inputs.request)
        .then((res) => {
            return res as AdminLaunchJobResponse;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};
