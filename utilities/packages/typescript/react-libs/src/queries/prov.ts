import { PROV_API_ENDPOINTS } from "./endpoints";
import { requests } from "../stores";
import {
  AddStudyLinkQueryParameters,
  AddStudyLinkResponse,
  PostUpdateModelRunInput,
  RegisterModelRunResponse,
} from "../provena-interfaces/AsyncJobAPI";

import { GenerateReportParameters, GenerateReportResponse } from "react-libs/provena-interfaces/ProvenanceAPI";

import { requestErrToMsg } from "../util";
import { ModelRunRecord } from "../provena-interfaces/RegistryModels";
import { PostUpdateModelRunResponse } from "../provena-interfaces/ProvenanceAPI";

export const addStudyLink = (inputs: {
  modelRunId: string;
  studyId: string;
}) => {
  const endpoint = PROV_API_ENDPOINTS.ADD_STUDY_LINK;
  return requests
    .post(endpoint, {}, {
      model_run_id: inputs.modelRunId,
      study_id: inputs.studyId,
    } as AddStudyLinkQueryParameters)
    .then((res) => {
      const resJson = res as AddStudyLinkResponse;
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


export const generateReport = (inputs: GenerateReportParameters) => {

  // Generate-report endpoints.
  const endpoint = PROV_API_ENDPOINTS.GENERATE_REPORT

  // Create the axios method. 
  return requests
  .get(endpoint, {
    node_id: inputs.node_id,
    depth: inputs.depth,
    item_subtype: inputs.item_subtype, 
    
  })
  .then((response) => {
    const responseJson = response as GenerateReportResponse
    // Check the status of the response. 
    try{ 
    
      if(!responseJson.status.success){
        return Promise.reject(response)
      } else{ 
        return responseJson
      }

    } catch (e){ 
      return Promise.reject(response)
    }

  })

  .catch((err) => { 
    return Promise.reject(requestErrToMsg(err))
  
  })
  
}
export const registerModelRunRecord = (inputs: { record: ModelRunRecord }) => {
  const endpoint = PROV_API_ENDPOINTS.REGISTER_MODEL_RUN_COMPLETE;
  return requests
    .post(endpoint, inputs.record)
    .then((res) => {
      const resJson = res as RegisterModelRunResponse;
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

export const updateModelRunRecord = (inputs: PostUpdateModelRunInput) => {
  // TODO
  const endpoint = PROV_API_ENDPOINTS.UPDATE_MODEL_RUN;
  return requests
    .post(endpoint, inputs)
    .then((res) => {
      return res as PostUpdateModelRunResponse;
    })
    .catch((err) => {
      return Promise.reject(requestErrToMsg(err));
    });
};
