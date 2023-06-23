/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type DatasetType = "DATA_STORE";
export type JobType = "LODGE_MODEL_RUN_RECORD";
export type JobStatus = "PENDING" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED";

export interface AssociationInfo {
  modeller_id: string;
  requesting_organisation_id?: string;
}
export interface BatchHistoryResponse {
  status: Status;
  batch_jobs?: BatchJob[];
}
export interface Status {
  success: boolean;
  details: string;
}
export interface BatchJob {
  batch_id: string;
  created_time: number;
  jobs: string[];
}
export interface BulkSubmission {
  jobs: ModelRunRecord[];
}
export interface ModelRunRecord {
  workflow_template_id: string;
  inputs: TemplatedDataset[];
  outputs: TemplatedDataset[];
  annotations?: {
    [k: string]: string;
  };
  description?: string;
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
export interface BulkSubmissionResponse {
  status: Status;
  jobs?: LodgeModelRunJobRequest[];
  batch_id?: string;
}
export interface LodgeModelRunJobRequest {
  id: string;
  username: string;
  job_type?: JobType & string;
  submitted_time: number;
  model_run_record: ModelRunRecord;
}
export interface ConvertModelRunsResponse {
  status: Status;
  new_records?: ModelRunRecord[];
  existing_records?: string[];
  warnings?: string[];
}
export interface DescribeBatchResponse {
  status: Status;
  job_info?: LodgeModelRunJob[];
  missing?: string[];
  all_successful: boolean;
}
export interface LodgeModelRunJob {
  id: string;
  job_status: JobStatus;
  error_info?: string;
  job_type?: JobType & string;
  created_time: number;
  updated_time: number;
  model_run_record_id?: string;
  model_run_record: ModelRunRecord;
  username: string;
}
export interface DescribeJobResponse {
  status: Status;
  job_info?: LodgeModelRunJob;
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
export interface RegisterModelRunResponse {
  status: Status;
  record_info?: ProvenanceRecordInfo;
}
export interface StatusResponse {
  status: Status;
}
export interface BatchRecord {
  username: string;
  batch_jobs: {
    [k: string]: BatchJob;
  };
}
export interface JobLogBase {
  id: string;
  job_status: JobStatus;
  error_info?: string;
  job_type: JobType;
  created_time: number;
  updated_time: number;
}
export interface JobRequestBase {
  id: string;
  username: string;
  job_type: JobType;
  submitted_time: number;
}
