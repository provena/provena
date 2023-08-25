import FileDownload from "js-file-download";
import {
    JOB_API_ENDPOINTS,
    PROV_API_ENDPOINTS,
    requestErrToMsg,
    requests,
    subtypeActionToEndpoint,
} from "react-libs";
// import FormData from "form-data";
import { PaginationKey } from "react-libs";
import {
    ListByBatchRequest,
    ListByBatchResponse,
} from "react-libs/shared-interfaces/AsyncJobAPI";
import { RegisterBatchModelRunResponse } from "react-libs/shared-interfaces/ProvenanceAPI";
import {
    ConvertModelRunsResponse,
    ModelRunRecord,
} from "../shared-interfaces/ProvenanceAPI";
import {
    ModelRunWorkflowTemplateListResponse,
    SubtypeListRequest,
} from "../shared-interfaces/RegistryAPI";

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
        .post(
            PROV_API_ENDPOINTS.SUBMIT_MODEL_RUNS,
            { records: records },
            {},
            true
        )
        .then((res) => {
            const resJson = res as RegisterBatchModelRunResponse;
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
