/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type ValueType = "DESC" | "URL";

export interface AddValueIndexRequest {
  value_type: ValueType;
  value: string;
  id: string;
  index: number;
}
export interface Handle {
  id: string;
  properties: HandleProperty[];
}
export interface HandleProperty {
  type: ValueType;
  value: string;
  index: number;
}
export interface AddValueRequest {
  value_type: ValueType;
  value: string;
  id: string;
}
export interface ListResponse {
  ids: string[];
}
export interface MintRequest {
  value_type: ValueType;
  value: string;
}
export interface ModifyRequest {
  id: string;
  index: number;
  value: string;
}
export interface RemoveRequest {
  id: string;
  index: number;
}
export interface StatusResponse {
  status: Status;
}
export interface Status {
  success: boolean;
  details: string;
}
export interface ValueRequestBase {
  value_type: ValueType;
  value: string;
}
export interface UserInfo {
  username: string;
  email: string;
  roles: string[];
}
export interface VersionDetails {
  commit_id?: string;
  commit_url?: string;
  tag_name?: string;
  release_title?: string;
  release_url?: string;
}
