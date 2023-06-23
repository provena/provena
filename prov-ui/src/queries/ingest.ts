import FileDownload from "js-file-download";
import { PROV_API_ENDPOINTS, subtypeActionToEndpoint } from "react-libs";
import { requests } from "react-libs";
// import FormData from "form-data";
import {
    BatchHistoryResponse,
    BulkSubmissionResponse,
    ConvertModelRunsResponse,
    DescribeBatchResponse,
    ModelRunRecord,
    StatusResponse,
} from "../shared-interfaces/ProvenanceAPI";
import {
    ModelRunWorkflowTemplateListResponse,
    SubtypeListRequest,
} from "../shared-interfaces/RegistryAPI";

function requestErrToMsg(err: any): string {
    console.log("Decoding " + err);
    try {
        let jsonStatus = err as StatusResponse;
        let details = jsonStatus.status.details;
        if (!!details) {
            return details;
        } else {
            throw new Error("Failed to parse repsonse as StatusResponse.");
        }
    } catch {
        var statusCode = "Unknown";
        var message = "Unknown - contact admin and check console";
        try {
            statusCode = err.status;
        } catch {}

        try {
            message = err.data.detail ? err.data.detail : "";
        } catch {}

        const msg = `Status code ${statusCode}. Error message: ${message}`;
        console.log("Error message: " + msg);
        return msg;
    }
}

export const getCSVTemplate = (workflow_template_id: string) => {
    return requests
        .csvDownload(PROV_API_ENDPOINTS.GENERATE_CSV_TEMPLATE, {
            workflow_template_id: workflow_template_id,
        })
        .then((res) => {
            // This is another promise
            return res.text();
        })
        .then((text) => {
            // This launches a download for the file
            FileDownload(text, "model_run_template.csv", "text/csv");
            // And resolves the content
            return text;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const uploadCSVTemplate = (csvFile: File) => {
    // Create the form data
    const expectedKey = "csv_file";
    const formData = new FormData();
    formData.append(expectedKey, csvFile);
    return requests
        .manual({
            url: PROV_API_ENDPOINTS.CONVERT_CSV_TEMPLATE,
            method: "post",
            data: formData,
            headers: { "Content-Type": "multipart/form-data" },
        })
        .then((res) => {
            const resJson = res as ConvertModelRunsResponse;
            if (!resJson.status.success) {
                return Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const submitModelRunRecords = (records: Array<ModelRunRecord>) => {
    return requests
        .post(PROV_API_ENDPOINTS.SUBMIT_MODEL_RUNS, { jobs: records }, {}, true)
        .then((res) => {
            const resJson = res as BulkSubmissionResponse;
            if (!resJson.status.success) {
                return Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const describeBatch = (batchId: string) => {
    return requests
        .get(PROV_API_ENDPOINTS.DESCRIBE_BATCH, { batch_id: batchId })
        .then((res) => {
            const resJson = res as DescribeBatchResponse;
            if (!resJson.status.success) {
                return Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const getBatchJobHistory = () => {
    return requests
        .get(PROV_API_ENDPOINTS.BATCH_HISTORY, {})
        .then((res) => {
            const resJson = res as BatchHistoryResponse;
            if (!resJson.status.success) {
                return Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};

export const getWorkflowTemplateList = () => {
    const payload: SubtypeListRequest = {};
    const endpoint = subtypeActionToEndpoint(
        "LIST",
        "MODEL_RUN_WORKFLOW_TEMPLATE"
    );
    return requests
        .post(endpoint, {})
        .then((res) => {
            let resJson = res as ModelRunWorkflowTemplateListResponse;
            if (!resJson.status.success) {
                Promise.reject(res);
            } else {
                return resJson;
            }
        })
        .catch((err) => {
            Promise.reject(requestErrToMsg(err));
        });
};

export const generateCsvFromBatchId = (batchId: string) => {
    return requests
        .csvDownload(PROV_API_ENDPOINTS.REGENERATE_FROM_BATCH, {
            batch_id: batchId,
        })
        .then((res) => {
            // This is another promise
            return res.text();
        })
        .then((text) => {
            // This launches a download for the file
            FileDownload(text, "updated_template.csv", "text/csv");
            // And resolves the content
            return text;
        })
        .catch((err) => {
            return Promise.reject(requestErrToMsg(err));
        });
};
