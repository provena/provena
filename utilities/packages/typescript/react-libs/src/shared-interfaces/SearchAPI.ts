/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type SearchResultType = "DATASET" | "REGISTRY_ITEM";

export interface MixedQueryResult {
  id: string;
  score: number;
  type: SearchResultType;
}
export interface MixedQueryResults {
  status: Status;
  results?: MixedQueryResult[];
  warnings?: string[];
}
export interface Status {
  success: boolean;
  details: string;
}
export interface QueryResult {
  id: string;
  score: number;
}
export interface QueryResults {
  status: Status;
  results?: QueryResult[];
  warnings?: string[];
}
export interface StatusResponse {
  status: Status;
}
export interface VersionDetails {
  commit_id?: string;
  commit_url?: string;
  tag_name?: string;
  release_title?: string;
  release_url?: string;
}
