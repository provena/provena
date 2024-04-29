import {
  SEARCH_API_ENDPOINTS,
  REGISTRY_STORE_GENERIC_API_ENDPOINTS,
} from "./endpoints";
import { requests } from "../stores";
import { QueryResults } from "../provena-interfaces/SearchAPI";
import { UntypedFetchResponse } from "../provena-interfaces/RegistryAPI";
import { ItemSubType } from "../provena-interfaces/RegistryModels";
import { requestErrToMsg } from "../util";

export const searchRegistry = (query: string, subtypeFilter?: ItemSubType) => {
  const endpoint = SEARCH_API_ENDPOINTS.SEARCH_REGISTRY;

  var params;
  if (subtypeFilter === undefined) {
    params = {
      query: query,
    };
  } else {
    params = {
      query: query,
      subtype_filter: subtypeFilter,
    };
  }

  return requests
    .get(endpoint, params)
    .then((res) => {
      const resJson = res as QueryResults;
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

export const fetchRegistryItem = (handle: string) => {
  const endpoint = REGISTRY_STORE_GENERIC_API_ENDPOINTS.FETCH_ITEM;
  const params = {
    id: handle,
  };
  return requests
    .get(endpoint, params)
    .then((res) => {
      const resJson = res as UntypedFetchResponse;
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
