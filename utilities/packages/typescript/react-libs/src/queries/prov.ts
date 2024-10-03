import { PROV_API_ENDPOINTS } from "./endpoints";
import { requests } from "../stores";
import {
  AddStudyLinkQueryParameters,
  AddStudyLinkResponse,
} from "../provena-interfaces/AsyncJobAPI";
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


export const exportGraph = (inputs: {
  nodeId: string;
  depth: string;
}) => {

  const endpoint = PROV_API_ENDPOINTS.EXPORT

  return requests
      .get (endpoint, ) 
  

}
