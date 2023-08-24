/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type DatasetType = "DATA_STORE";

export interface AssociationInfo {
  modeller_id: string;
  requesting_organisation_id?: string;
}
export interface ConvertModelRunsResponse {
  status: Status;
  new_records?: ModelRunRecord[];
  existing_records?: string[];
  warnings?: string[];
}
export interface Status {
  success: boolean;
  details: string;
}
export interface ModelRunRecord {
  workflow_template_id: string;
  inputs: TemplatedDataset[];
  outputs: TemplatedDataset[];
  annotations?: {
    [k: string]: string;
  };
  display_name: string;
  description: string;
  associations: AssociationInfo;
  start_time: number;
  end_time: number;
}
export interface TemplatedDataset {
  dataset_template_id: string;
  dataset_id: string;
  dataset_type: DatasetType;
  resources?: {
    [k: string]: string;
  };
}
export interface LineageResponse {
  status: Status;
  record_count?: number;
  graph?: {
    [k: string]: unknown;
  };
}
export interface ProvenanceRecordInfo {
  id: string;
  prov_json: string;
  record: ModelRunRecord;
}
export interface RegisterBatchModelRunRequest {
  records: ModelRunRecord[];
}
export interface RegisterBatchModelRunResponse {
  status: Status;
  session_id?: string;
}
export interface RegisterModelRunResponse {
  status: Status;
  session_id?: string;
}
export interface StatusResponse {
  status: Status;
}
export interface SyncRegisterModelRunResponse {
  status: Status;
  record_info: ProvenanceRecordInfo;
}
export interface VersionDetails {
  commit_id?: string;
  commit_url?: string;
  tag_name?: string;
  release_title?: string;
  release_url?: string;
}
