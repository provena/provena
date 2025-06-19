import axios from "axios";
import { keycloak } from "./keycloak";
import * as Sentry from "@sentry/react";

//@ts-ignore
export const apiagent = (options) => {
  // This relies on keycloak being setup properly and injected in the
  // consuming library!
  if (keycloak.authenticated) {
    axios.defaults.headers.common["Authorization"] = "Bearer " + keycloak.token;
  }
  axios.defaults.headers.common["Content-Type"] = "application/json";

  const request = axios.create();

  // Add a request interceptor
  request.interceptors.request.use(
    (requestConfig) => requestConfig,
    (requestError) => {
      return Promise.reject(requestError);
    },
  );

  //@ts-ignore
  const onSuccess = function (response) {
    console.debug("Request Successful!", response);
    return response.data;
  };

  //@ts-ignore
  const onError = function (error) {
    console.error("Request Failed:", error.config);

    if (error.response) {
      // Request was made but server responded with something
      // other than 2xx
      console.error("Status:", error.response.status);
      console.error("Data:", error.response.data);
      console.error("Headers:", error.response.headers);
    } else {
      // Something else happened while setting up the request
      // triggered the error
      console.error("Error Message:", error.message);
    }

    // Sentry monitoring: capture and pass the caught Axios Error object as an event to Sentry.
    // This will log all errors from any API utilizing this apiagent.
    Sentry.captureException(error);

    return Promise.reject(error.response);
  };

  return request(options).then(onSuccess).catch(onError);
};

/**
 * Base HTTP Client
 */
export const requests = {
  get(url: string, params = {}) {
    return apiagent({
      url: url,
      method: "get",
      params: params,
    });
  },

  delete(url: string, body = {}, params = {}) {
    return apiagent({
      url: url,
      body: body,
      method: "delete",
      params: params,
    });
  },

  post(
    url: string,
    data = {},
    params = {},
    config = {},
    errorOptout: boolean = false,
  ) {
    return apiagent({
      url: url,
      method: "post",
      data: data,
      config: config,
      params: params,
    });
  },

  put(url: string, data = {}, params = {}) {
    return apiagent({
      url: url,
      method: "put",
      data: data,
      params: params,
    });
  },

  patch(url: string, data = {}, errorOptout: boolean = false) {
    return apiagent({
      url: url,
      method: "patch",
      data: data,
    });
  },
  csvDownload(url: string, params = {}) {
    return apiagent({
      url: url,
      method: "get",
      responseType: "blob",
      params: params,
    });
  },
  fileDownload(url: string, data = {}){
    return apiagent({
      url: url, 
      method: "post",
      data: data,
      responseType: "blob",
      headers: {
      "Accept": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // Set Accept header for Word document
    }
    });
  },
  manual(config = {}) {
    return apiagent(config);
  },
};
