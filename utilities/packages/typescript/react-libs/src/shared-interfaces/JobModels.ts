/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type JobStatus = "PENDING" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED";
export type JobType = "LODGE_MODEL_RUN_RECORD";
export type DatasetType = "DATA_STORE";

export interface BatchJob {
  batch_id: string;
  created_time: number;
  jobs: string[];
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
export interface AssociationInfo {
  modeller_id: string;
  requesting_organisation_id?: string;
}
export interface LodgeModelRunJobRequest {
  id: string;
  username: string;
  job_type?: JobType & string;
  submitted_time: number;
  model_run_record: ModelRunRecord;
}
