/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type ItemCategory = "ACTIVITY" | "AGENT" | "ENTITY";
export type ItemSubType =
  | "WORKFLOW_RUN"
  | "MODEL_RUN"
  | "CREATE"
  | "VERSION"
  | "PERSON"
  | "ORGANISATION"
  | "SOFTWARE"
  | "MODEL"
  | "WORKFLOW_TEMPLATE"
  | "MODEL_RUN_WORKFLOW_TEMPLATE"
  | "DATASET"
  | "DATASET_TEMPLATE";
export type RecordType = "SEED_ITEM" | "COMPLETE_ITEM";
export type ResourceUsageType = "PARAMETER_FILE" | "CONFIG_FILE" | "FORCING_DATA" | "GENERAL_DATA";
export type WorkflowRunCompletionStatus = "INCOMPLETE" | "COMPLETE" | "LODGED";
export type DatasetType = "DATA_STORE";
export type LockActionType = "LOCK" | "UNLOCK";

export interface AccessInfo {
  reposited: boolean;
  uri?: string;
  description?: string;
}
export interface AccessSettings {
  owner: string;
  general: string[];
  groups: {
    [k: string]: string[];
  };
}
export interface ActivityBase {
  history: HistoryEntryDomainInfoBase[];
  display_name: string;
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryDomainInfoBase {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: DomainInfoBase;
}
export interface DomainInfoBase {
  display_name: string;
}
export interface WorkflowLinks {
  create_activity_workflow_id?: string;
  version_activity_workflow_id?: string;
}
export interface VersioningInfo {
  previous_version?: string;
  version: number;
  reason?: string;
  next_version?: string;
}
export interface AgentBase {
  history: HistoryEntryDomainInfoBase[];
  display_name: string;
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface AuthTableEntry {
  id: string;
  access_settings: AccessSettings;
}
export interface AutomationSchedule {}
export interface CollectionFormat {
  associations: CollectionFormatAssociations;
  dataset_info: CollectionFormatDatasetInfo;
  approvals: CollectionFormatApprovals;
}
export interface CollectionFormatAssociations {
  organisation_id: string;
}
export interface CollectionFormatDatasetInfo {
  name: string;
  description: string;
  access_info: AccessInfo;
  publisher_id: string;
  created_date: string;
  published_date: string;
  license: string;
  preferred_citation?: string;
  keywords?: string[];
  version?: string;
}
export interface CollectionFormatApprovals {
  ethics_registration: DatasetEthicsRegistrationCheck;
  ethics_access: DatasetEthicsAccessCheck;
  indigenous_knowledge: IndigenousKnowledgeCheck;
  export_controls: ExportControls;
}
export interface DatasetEthicsRegistrationCheck {
  relevant?: boolean;
  obtained?: boolean;
}
export interface DatasetEthicsAccessCheck {
  relevant?: boolean;
  obtained?: boolean;
}
export interface IndigenousKnowledgeCheck {
  relevant?: boolean;
  obtained?: boolean;
}
export interface ExportControls {
  relevant?: boolean;
  obtained?: boolean;
}
export interface CollectionFormatOrganisation {
  name: string;
  ror?: string;
}
export interface CreateDomainInfo {
  display_name: string;
  created_item_id: string;
}
export interface DatasetDomainInfo {
  display_name: string;
  collection_format: CollectionFormat;
  s3: S3Location;
}
export interface S3Location {
  bucket_name: string;
  path: string;
  s3_uri: string;
}
export interface DatasetParameter {
  parameter_name?: string;
  column_name?: string;
  column_index?: number;
  description?: string;
  vocabulary_id?: string;
}
export interface DatasetTemplateDomainInfo {
  display_name: string;
  description?: string;
  defined_resources?: DefinedResource[];
  deferred_resources?: DeferredResource[];
}
export interface DefinedResource {
  path: string;
  description: string;
  usage_type: ResourceUsageType;
  optional?: boolean;
  is_folder?: boolean;
  additional_metadata?: {
    [k: string]: string;
  };
}
export interface DeferredResource {
  key: string;
  description: string;
  usage_type: ResourceUsageType;
  optional?: boolean;
  is_folder?: boolean;
  additional_metadata?: {
    [k: string]: string;
  };
}
export interface DescribedRole {
  role_display_name: string;
  role_name: string;
  description: string;
  also_grants: string[];
}
export interface EntityBase {
  history: HistoryEntryDomainInfoBase[];
  display_name: string;
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryBaseDomainInfoBase {
  history: HistoryEntryDomainInfoBase[];
}
export interface HistoryEntryAny {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item?: unknown;
}
export interface ItemBase {
  history: HistoryEntryDomainInfoBase[];
  display_name: string;
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category: ItemCategory;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface ItemCreate {
  display_name: string;
  created_item_id: string;
  history: HistoryEntryCreateDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryCreateDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: CreateDomainInfo;
}
export interface ItemDataset {
  display_name: string;
  collection_format: CollectionFormat;
  s3: S3Location;
  history: HistoryEntryDatasetDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryDatasetDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: DatasetDomainInfo;
}
export interface ItemDatasetTemplate {
  display_name: string;
  description?: string;
  defined_resources?: DefinedResource[];
  deferred_resources?: DeferredResource[];
  history: HistoryEntryDatasetTemplateDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryDatasetTemplateDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: DatasetTemplateDomainInfo;
}
export interface ItemModel {
  display_name: string;
  name: string;
  description: string;
  documentation_url: string;
  source_url: string;
  history: HistoryEntryModelDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryModelDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: ModelDomainInfo;
}
export interface ModelDomainInfo {
  display_name: string;
  name: string;
  description: string;
  documentation_url: string;
  source_url: string;
}
export interface ItemModelRun {
  display_name: string;
  record_status: WorkflowRunCompletionStatus;
  record: ModelRunRecord;
  prov_serialisation: string;
  history: HistoryEntryModelRunDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
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
export interface AssociationInfo {
  modeller_id: string;
  requesting_organisation_id?: string;
}
export interface HistoryEntryModelRunDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: ModelRunDomainInfo;
}
export interface ModelRunDomainInfo {
  display_name: string;
  record_status: WorkflowRunCompletionStatus;
  record: ModelRunRecord;
  prov_serialisation: string;
}
export interface ItemModelRunWorkflowTemplate {
  display_name: string;
  software_id: string;
  software_version: string;
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
  history: HistoryEntryModelRunWorkflowTemplateDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface TemplateResource {
  template_id: string;
  optional?: boolean;
}
export interface WorkflowTemplateAnnotations {
  required?: string[];
  optional?: string[];
}
export interface HistoryEntryModelRunWorkflowTemplateDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: ModelRunWorkflowTemplateDomainInfo;
}
export interface ModelRunWorkflowTemplateDomainInfo {
  display_name: string;
  software_id: string;
  software_version: string;
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
}
export interface ItemOrganisation {
  display_name: string;
  name: string;
  ror?: string;
  history: HistoryEntryOrganisationDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryOrganisationDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: OrganisationDomainInfo;
}
export interface OrganisationDomainInfo {
  display_name: string;
  name: string;
  ror?: string;
}
export interface ItemPerson {
  display_name: string;
  email: string;
  first_name: string;
  last_name: string;
  orcid?: string;
  ethics_approved?: boolean;
  history: HistoryEntryPersonDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryPersonDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: PersonDomainInfo;
}
export interface PersonDomainInfo {
  display_name: string;
  email: string;
  first_name: string;
  last_name: string;
  orcid?: string;
  ethics_approved?: boolean;
}
export interface ItemSoftware {
  display_name: string;
  name: string;
  description: string;
  documentation_url: string;
  source_url: string;
  history: HistoryEntrySoftwareDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntrySoftwareDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: SoftwareDomainInfo;
}
export interface SoftwareDomainInfo {
  display_name: string;
  name: string;
  description: string;
  documentation_url: string;
  source_url: string;
}
export interface ItemVersion {
  display_name: string;
  reason: string;
  from_item_id: string;
  to_item_id: string;
  new_version_number: number;
  history: HistoryEntryVersionDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryVersionDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: VersionDomainInfo;
}
export interface VersionDomainInfo {
  display_name: string;
  reason: string;
  from_item_id: string;
  to_item_id: string;
  new_version_number: number;
}
export interface ItemWorkflowRun {
  display_name: string;
  record_status: WorkflowRunCompletionStatus;
  history: HistoryEntryWorkflowRunDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryWorkflowRunDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: WorkflowRunDomainInfo;
}
export interface WorkflowRunDomainInfo {
  display_name: string;
  record_status: WorkflowRunCompletionStatus;
}
export interface ItemWorkflowTemplate {
  display_name: string;
  software_id: string;
  software_version: string;
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
  history: HistoryEntryWorkflowTemplateDomainInfo[];
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category?: ItemCategory & string;
  item_subtype?: ItemSubType & string;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface HistoryEntryWorkflowTemplateDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: WorkflowTemplateDomainInfo;
}
export interface WorkflowTemplateDomainInfo {
  display_name: string;
  software_id: string;
  software_version: string;
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
}
export interface LockEvent {
  action_type: LockActionType;
  username: string;
  email?: string;
  reason: string;
  timestamp: number;
}
export interface LockInformation {
  locked: boolean;
  history: LockEvent[];
}
export interface LockTableEntry {
  id: string;
  lock_information: LockInformation;
}
export interface OptionallyRequiredCheck {
  relevant?: boolean;
  obtained?: boolean;
}
export interface RecordInfo {
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category: ItemCategory;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
export interface ResourceSpatialMetadata {}
export interface ResourceTemporalMetadata {
  start_time: number;
  end_time: number;
}
export interface SeededItem {
  id: string;
  owner_username: string;
  created_timestamp: number;
  updated_timestamp: number;
  item_category: ItemCategory;
  item_subtype: ItemSubType;
  record_type: RecordType;
  workflow_links?: WorkflowLinks;
  versioning_info?: VersioningInfo;
}
