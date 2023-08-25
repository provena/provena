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
export type ReleaseAction = "REQUEST" | "APPROVE" | "REJECT";
export type ReleasedStatus = "NOT_RELEASED" | "PENDING" | "RELEASED";
export type ResourceUsageType = "PARAMETER_FILE" | "CONFIG_FILE" | "FORCING_DATA" | "GENERAL_DATA";
export type QueryRecordTypes = "ALL" | "SEED_ONLY" | "COMPLETE_ONLY";
export type QueryDatasetReleaseStatusType = "NOT_RELEASED" | "PENDING" | "RELEASED";
export type SortType = "CREATED_TIME" | "UPDATED_TIME" | "DISPLAY_NAME" | "RELEASE_TIMESTAMP";
export type WorkflowRunCompletionStatus = "INCOMPLETE" | "COMPLETE" | "LODGED";
export type DatasetType = "DATA_STORE";
export type LockActionType = "LOCK" | "UNLOCK";
export type ImportMode =
  | "ADD_ONLY"
  | "ADD_OR_OVERWRITE"
  | "OVERWRITE_ONLY"
  | "SYNC_ADD_OR_OVERWRITE"
  | "SYNC_DELETION_ALLOWED";

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
export interface AuthRolesResponse {
  roles: DescribedRole[];
}
export interface DescribedRole {
  role_display_name: string;
  role_name: string;
  description: string;
  also_grants: string[];
}
export interface AuthTableEntry {
  id: string;
  access_settings: AccessSettings;
}
export interface AutomationSchedule {}
export interface BundledItem {
  id: string;
  item_payload: {
    [k: string]: unknown;
  };
  auth_payload: {
    [k: string]: unknown;
  };
  lock_payload: {
    [k: string]: unknown;
  };
}
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
export interface CreateFetchResponse {
  status: Status;
  item?: ItemCreate | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface Status {
  success: boolean;
  details: string;
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
export interface CreateListResponse {
  status: Status;
  items?: ItemCreate[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface DatasetCreateResponse {
  status: Status;
  created_item?: ItemDataset;
  register_create_activity_session_id?: string;
}
export interface ItemDataset {
  display_name: string;
  collection_format: CollectionFormat;
  s3: S3Location;
  release_history?: ReleaseHistoryEntry[];
  release_status: ReleasedStatus;
  release_approver?: string;
  release_timestamp?: number;
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
export interface S3Location {
  bucket_name: string;
  path: string;
  s3_uri: string;
}
export interface ReleaseHistoryEntry {
  action: ReleaseAction;
  timestamp: number;
  approver: string;
  requester?: string;
  notes: string;
}
export interface HistoryEntryDatasetDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: DatasetDomainInfo;
}
export interface DatasetDomainInfo {
  display_name: string;
  collection_format: CollectionFormat;
  s3: S3Location;
  release_history?: ReleaseHistoryEntry[];
  release_status: ReleasedStatus;
  release_approver?: string;
  release_timestamp?: number;
}
export interface DatasetFetchResponse {
  status: Status;
  item?: ItemDataset | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface DatasetListResponse {
  status: Status;
  items?: ItemDataset[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface DatasetParameter {
  parameter_name?: string;
  column_name?: string;
  column_index?: number;
  description?: string;
  vocabulary_id?: string;
}
export interface DatasetSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface DatasetTemplateCreateResponse {
  status: Status;
  created_item?: ItemDatasetTemplate;
  register_create_activity_session_id?: string;
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
export interface HistoryEntryDatasetTemplateDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: DatasetTemplateDomainInfo;
}
export interface DatasetTemplateDomainInfo {
  display_name: string;
  description?: string;
  defined_resources?: DefinedResource[];
  deferred_resources?: DeferredResource[];
}
export interface DatasetTemplateFetchResponse {
  status: Status;
  item?: ItemDatasetTemplate | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface DatasetTemplateListResponse {
  status: Status;
  items?: ItemDatasetTemplate[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface DatasetTemplateSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface DescribeAccessResponse {
  roles: string[];
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
export interface FetchItemRequest {
  item_id: string;
}
export interface FilterOptions {
  record_type?: QueryRecordTypes & string;
  item_subtype?: ItemSubType;
  release_reviewer?: string;
  release_status?: QueryDatasetReleaseStatusType;
}
export interface GeneralListRequest {
  filter_by?: FilterOptions;
  sort_by?: SortOptions;
  pagination_key?: {
    [k: string]: unknown;
  };
  page_size?: number;
}
export interface SortOptions {
  sort_type?: SortType;
  ascending?: boolean;
}
export interface GenericCreateResponse {
  status: Status;
  created_item?: ItemBase;
  register_create_activity_session_id?: string;
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
export interface GenericFetchResponse {
  status: Status;
  item?: ItemBase | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface GenericListResponse {
  status: Status;
  items?: unknown[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface GenericSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
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
export interface ItemRevertRequest {
  id: string;
  history_id: number;
  reason: string;
}
export interface ItemRevertResponse {
  status: Status;
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
export interface JsonSchemaResponse {
  status: Status;
  json_schema?: {
    [k: string]: unknown;
  };
}
export interface ListUserReviewingDatasetsRequest {
  pagination_key?: {
    [k: string]: unknown;
  };
  page_size?: number;
  sort_by?: SortOptions;
  filter_by: FilterOptions;
}
export interface LockChangeRequest {
  id: string;
  reason: string;
}
export interface LockEvent {
  action_type: LockActionType;
  username: string;
  email?: string;
  reason: string;
  timestamp: number;
}
export interface LockHistoryResponse {
  status: Status;
  history?: LockEvent[];
}
export interface LockInformation {
  locked: boolean;
  history: LockEvent[];
}
export interface LockStatusResponse {
  locked: boolean;
}
export interface LockTableEntry {
  id: string;
  lock_information: LockInformation;
}
export interface ModelCreateResponse {
  status: Status;
  created_item?: ItemModel;
  register_create_activity_session_id?: string;
}
export interface ModelFetchResponse {
  status: Status;
  item?: ItemModel | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface ModelListResponse {
  status: Status;
  items?: ItemModel[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface ModelRunCreateResponse {
  status: Status;
  created_item?: ItemModelRun;
  register_create_activity_session_id?: string;
}
export interface ModelRunFetchResponse {
  status: Status;
  item?: ItemModelRun | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface ModelRunListResponse {
  status: Status;
  items?: ItemModelRun[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface ModelRunSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface ModelRunWorkflowTemplateCreateResponse {
  status: Status;
  created_item?: ItemModelRunWorkflowTemplate;
  register_create_activity_session_id?: string;
}
export interface ModelRunWorkflowTemplateFetchResponse {
  status: Status;
  item?: ItemModelRunWorkflowTemplate | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface ModelRunWorkflowTemplateListResponse {
  status: Status;
  items?: ItemModelRunWorkflowTemplate[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface ModelRunWorkflowTemplateSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface ModelSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface NoFilterSubtypeListRequest {
  sort_by?: SortOptions;
  pagination_key?: {
    [k: string]: unknown;
  };
  page_size?: number;
}
export interface OptionallyRequiredCheck {
  relevant?: boolean;
  obtained?: boolean;
}
export interface OrganisationCreateResponse {
  status: Status;
  created_item?: ItemOrganisation;
  register_create_activity_session_id?: string;
}
export interface OrganisationFetchResponse {
  status: Status;
  item?: ItemOrganisation | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface OrganisationListResponse {
  status: Status;
  items?: ItemOrganisation[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface OrganisationSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface PaginatedDatasetListResponse {
  status: Status;
  dataset_items?: ItemDataset[];
  total_dataset_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface PaginatedListResponse {
  status: Status;
  items?: unknown[];
  total_item_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface PersonCreateResponse {
  status: Status;
  created_item?: ItemPerson;
  register_create_activity_session_id?: string;
}
export interface PersonFetchResponse {
  status: Status;
  item?: ItemPerson | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface PersonListResponse {
  status: Status;
  items?: ItemPerson[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface PersonSeedResponse {
  status: Status;
  seeded_item?: SeededItem;
}
export interface ProxyItemFetchRequest {
  item_id: string;
  username: string;
}
export interface ProxyVersionRequest {
  id: string;
  reason: string;
  username: string;
}
export interface QueryFilter {
  item_category?: ItemCategory;
  item_subtype?: ItemSubType;
  record_type?: QueryRecordTypes & string;
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
export interface RegistryExportResponse {
  status: Status;
  items?: BundledItem[];
}
export interface RegistryImportRequest {
  import_mode: ImportMode;
  parse_items?: boolean;
  allow_entry_deletion?: boolean;
  trial_mode?: boolean;
  items: BundledItem[];
}
export interface RegistryImportResponse {
  status: Status;
  trial_mode: boolean;
  statistics?: RegistryImportStatistics;
  failure_list?: [
    string,
    {
      [k: string]: unknown;
    }
  ][];
}
export interface RegistryImportStatistics {
  old_registry_size: number;
  new_registry_size: number;
  deleted_entries: number;
  overwritten_entries: number;
  new_entries: number;
}
export interface RegistryImportSettings {
  import_mode: ImportMode;
  parse_items?: boolean;
  allow_entry_deletion?: boolean;
  trial_mode?: boolean;
}
export interface RegistryRestoreRequest {
  import_mode: ImportMode;
  parse_items?: boolean;
  allow_entry_deletion?: boolean;
  trial_mode?: boolean;
  table_names: TableNames;
}
export interface TableNames {
  resource_table_name: string;
  auth_table_name: string;
  lock_table_name: string;
}
export interface ResourceSpatialMetadata {}
export interface ResourceTemporalMetadata {
  start_time: number;
  end_time: number;
}
export interface SchemaResponse {
  json_schema: {
    [k: string]: unknown;
  };
}
export interface StatusResponse {
  status: Status;
}
export interface SubtypeFilterOptions {
  record_type?: QueryRecordTypes & string;
}
export interface SubtypeListRequest {
  filter_by?: SubtypeFilterOptions;
  sort_by?: SortOptions;
  pagination_key?: {
    [k: string]: unknown;
  };
  page_size?: number;
}
export interface UiSchemaResponse {
  status: Status;
  ui_schema?: {
    [k: string]: unknown;
  };
}
export interface UntypedFetchResponse {
  status: Status;
  item?: {
    [k: string]: unknown;
  };
}
export interface UpdateResponse {
  status: Status;
  register_create_activity_session_id?: string;
}
export interface VersionFetchResponse {
  status: Status;
  item?: ItemVersion | SeededItem;
  roles?: string[];
  locked?: boolean;
  item_is_seed?: boolean;
}
export interface VersionListResponse {
  status: Status;
  items?: ItemVersion[];
  seed_items?: SeededItem[];
  unparsable_items?: {
    [k: string]: unknown;
  }[];
  total_item_count?: number;
  complete_item_count?: number;
  seed_item_count?: number;
  unparsable_item_count?: number;
  not_authorised_count?: number;
  pagination_key?: {
    [k: string]: unknown;
  };
}
export interface VersionRequest {
  id: string;
  reason: string;
}
export interface VersionResponse {
  new_version_id: string;
  version_job_session_id: string;
}
export interface VersionDetails {
  commit_id?: string;
  commit_url?: string;
  tag_name?: string;
  release_title?: string;
  release_url?: string;
}
