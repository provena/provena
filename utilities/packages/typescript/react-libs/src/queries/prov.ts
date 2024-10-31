import { PROV_API_ENDPOINTS } from "./endpoints";
import { requests } from "../stores";
import {
  AddStudyLinkQueryParameters,
  AddStudyLinkResponse,
} from "../provena-interfaces/AsyncJobAPI";
import FileDownload from "js-file-download";

import { GenerateReportParameters} from "react-libs/provena-interfaces/ProvenanceAPI";
import { requestErrToMsg } from "../util";

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
  .fileDownload(endpoint, {
    id: inputs.id,
    depth: inputs.depth,
    item_subtype: inputs.item_subtype,    
  })
  .then((response) => {
    // Check the status of the response - The Response is a blob itself.

    try{ 

      if(!response){
        return Promise.reject(response)
      } else{
        return FileDownload(response, "study-close-out-report.docx")
      }

    } catch (e){ 
      return Promise.reject(response)
    }

  })
  .catch((err) => { 
    return Promise.reject(requestErrToMsg(err))
  
  })
  
}