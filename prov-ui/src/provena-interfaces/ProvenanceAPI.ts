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
  | "STUDY"
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
export type DatasetType = "DATA_STORE";
export type ReleaseAction = "REQUEST" | "APPROVE" | "REJECT";
export type ReleasedStatus = "NOT_RELEASED" | "PENDING" | "RELEASED";
export type ResourceUsageType = "PARAMETER_FILE" | "CONFIG_FILE" | "FORCING_DATA" | "GENERAL_DATA";
export type WorkflowRunCompletionStatus = "INCOMPLETE" | "COMPLETE" | "LODGED";
export type LockActionType = "LOCK" | "UNLOCK";

/**
 * Please specify whether data is going to be stored in the Data Store, or referenced from an existing, externally hosted, source.
 */
export interface AccessInfo {
  /**
   * Is the data going to be stored in the Data Store?
   */
  reposited?: boolean;
  /**
   * Provide the best URI of the externally hosted data.
   */
  uri?: string;
  /**
   * Provide information about how to access the externally hosted data, or other relevant notes.
   */
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
export interface AddStudyLinkQueryParameters {
  model_run_id: string;
  study_id: string;
}
export interface AddStudyLinkResponse {
  status: Status;
  model_run_id: string;
  study_id: string;
  session_id: string;
}
export interface Status {
  success: boolean;
  details: string;
}
export interface AgentBase {
  history: HistoryEntryDomainInfoBase[];
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
export interface AssociationInfo {
  modeller_id: string;
  requesting_organisation_id?: string;
}
export interface AuthTableEntry {
  id: string;
  access_settings: AccessSettings;
}
export interface AutomationSchedule {}
/**
 * This form collects metadata about the dataset you are registering as well as the registration itself. Please ensure the fields below are completed accurately.
 */
export interface DatasetMetadata {
  associations: DatasetAssociations;
  approvals: DatasetApprovals;
  dataset_info: DatasetInformation;
}
/**
 * Please provide information about the people and organisations related to this dataset.
 */
export interface DatasetAssociations {
  /**
   * Please select the organisation on behalf of which you are registering this data.
   */
  organisation_id: string;
  /**
   * Please select the Registered Person who is the dataset custodian.
   */
  data_custodian_id?: string;
  /**
   * Please provide a point of contact for enquiries about this data e.g. email address. Please ensure you have sought consent to include these details in the record.
   */
  point_of_contact?: string;
}
/**
 * Please ensure that the following approvals are considered. Your dataset may not be fit for inclusion in the Data Store if it does not meet the following requirements.
 */
export interface DatasetApprovals {
  ethics_registration: DatasetRegistrationEthicsAndPrivacy;
  ethics_access: DatasetAccessEthicsAndPrivacy;
  indigenous_knowledge: IndigenousKnowledgeAndConsent;
  export_controls: ExportControls;
}
/**
 * Does this dataset include any human data or require ethics/privacy approval for its registration? If so, have you included any required ethics approvals, consent from the participants and/or appropriate permissions to register this dataset in this information system?
 */
export interface DatasetRegistrationEthicsAndPrivacy {
  relevant?: boolean;
  obtained?: boolean;
}
/**
 * Does this dataset include any human data or require ethics/privacy approval for enabling its access by users of the information system? If so, have you included any required consent from the participants and/or appropriate permissions to facilitate access to this dataset in this information system?
 */
export interface DatasetAccessEthicsAndPrivacy {
  relevant?: boolean;
  obtained?: boolean;
}
/**
 * Does this dataset contain Indigenous Knowledge? If so, do you have consent from the relevant Aboriginal and Torres Strait Islander communities for its use and access via this data store?
 */
export interface IndigenousKnowledgeAndConsent {
  relevant?: boolean;
  obtained?: boolean;
}
/**
 * Is this dataset subject to any export controls permits? If so, has this dataset cleared any required due diligence checks and have you obtained any required permits?
 */
export interface ExportControls {
  relevant?: boolean;
  obtained?: boolean;
}
/**
 * Please provide information about this dataset, including the name, description, creation date and publisher information.
 */
export interface DatasetInformation {
  /**
   * Please provide a readable name for the dataset.
   */
  name: string;
  /**
   * Please provide a more detailed description of the dataset. This should include the nature of the data, the intended usage, and any other relevant information.
   */
  description: string;
  access_info: AccessInfo;
  /**
   * Please provide information about the organisation which is publishing or producing this dataset. If this is your organisation, please select it again using the tool below.
   */
  publisher_id: string;
  created_date: DatasetCreationDate;
  published_date: DatasetPublicationDate;
  /**
   * Please select a standard license for usage, by default it will be 'Copyright'.
   */
  license: string;
  /**
   * A brief description of the reason a data asset was created. Should be a good guide to the potential usefulness of a data asset to other users.
   */
  purpose?: string;
  /**
   * Specify the party owning or managing rights over the resource. Please ensure you have sought consent to include these details in the record.
   */
  rights_holder?: string;
  /**
   * A statement that provides information on any caveats or restrictions on access or on the use of the data asset, including legal, security, privacy, commercial or other limitations.
   */
  usage_limitations?: string;
  /**
   * If you would like to specify how this dataset should be cited, please use the checkbox below to indicate this preference, and enter your preferred citation in the text box.
   */
  preferred_citation?: string;
  spatial_info?: DatasetSpatialInformation;
  temporal_info?: DatasetTemporalInformation;
  /**
   * What file formats are present in this dataset? E.g. "pdf", "csv" etc.
   */
  formats?: string[];
  /**
   * Provide a list of keywords which describe your dataset [Optional].
   */
  keywords?: string[];
  /**
   * Optionally provide a collection of key value annotations for this dataset.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
/**
 * Has the dataset been created? If so, please provide the date on which this version of the dataset was produced or generated.
 */
export interface DatasetCreationDate {
  relevant?: boolean;
  value?: string;
}
/**
 * Has the dataset been published? If so, please provide the date on which this version of the dataset was first published.
 */
export interface DatasetPublicationDate {
  relevant?: boolean;
  value?: string;
}
/**
 * If your dataset includes spatial data, you can indicate the coverage, resolution and extent of this spatial data.
 */
export interface DatasetSpatialInformation {
  /**
   * The geographic area applicable to the data asset. Please specify spatial coverage using the EWKT format.
   */
  coverage?: string;
  /**
   * The spatial resolution applicable to the data asset. Please use the Decimal Degrees standard.
   */
  resolution?: string;
  /**
   * The range of spatial coordinates applicable to the data asset. Please provide a bounding box extent using the EWKT format.
   */
  extent?: string;
}
/**
 * If your dataset provides data over a specified time period, you can include the duration and resolution of this temporal coverage.
 */
export interface DatasetTemporalInformation {
  duration?: TemporalDuration;
  /**
   * The temporal resolution (i.e. time step) of the data. Please use the [ISO8601 duration format](https://en.wikipedia.org/wiki/ISO_8601#Durations) e.g. "P1Y2M10DT2H30M".
   */
  resolution?: string;
}
/**
 * You can specify the duration of temporal coverage by including both start and end date.
 */
export interface TemporalDuration {
  /**
   * Please provide the start date of the dataset's temporal coverage.
   */
  begin_date: string;
  /**
   * Please provide the end date of the dataset's temporal coverage.
   */
  end_date: string;
}
export interface ConvertModelRunsResponse {
  status: Status;
  new_records?: ModelRunRecord[];
  existing_records?: string[];
  warnings?: string[];
}
export interface ModelRunRecord {
  workflow_template_id: string;
  model_version?: string;
  inputs: TemplatedDataset[];
  outputs: TemplatedDataset[];
  annotations?: {
    [k: string]: string;
  };
  display_name: string;
  description: string;
  study_id?: string;
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
export interface CreateDomainInfo {
  display_name: string;
  created_item_id: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface DatasetDomainInfo {
  display_name: string;
  collection_format: DatasetMetadata;
  s3: S3Location;
  release_history?: ReleaseHistoryEntry[];
  release_status: ReleasedStatus;
  release_approver?: string;
  release_timestamp?: number;
  access_info_uri?: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
export interface GenerateReportRequest {
  id: string;
  item_subtype: ItemSubType;
  depth: number;
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  collection_format: DatasetMetadata;
  s3: S3Location;
  release_history?: ReleaseHistoryEntry[];
  release_status: ReleasedStatus;
  release_approver?: string;
  release_timestamp?: number;
  access_info_uri?: string;
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemModelRun {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemModelRunWorkflowTemplate {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  software_id: string;
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
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemOrganisation {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemPerson {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemSoftware {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  name: string;
  description: string;
  documentation_url: string;
  source_url: string;
}
export interface ItemStudy {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  title: string;
  description: string;
  study_alternative_id?: string;
  history: HistoryEntryStudyDomainInfo[];
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
export interface HistoryEntryStudyDomainInfo {
  id: number;
  timestamp: number;
  reason: string;
  username: string;
  item: StudyDomainInfo;
}
export interface StudyDomainInfo {
  display_name: string;
  title: string;
  description: string;
  study_alternative_id?: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemVersion {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
}
export interface ItemWorkflowRun {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  record_status: WorkflowRunCompletionStatus;
}
export interface ItemWorkflowTemplate {
  display_name: string;
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  software_id: string;
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
  /**
   * Optionally provide a collection of key value annotations describing this resource.
   */
  user_metadata?: {
    [k: string]: string;
  };
  software_id: string;
  input_templates?: TemplateResource[];
  output_templates?: TemplateResource[];
  annotations?: WorkflowTemplateAnnotations;
}
export interface LineageResponse {
  status: Status;
  record_count?: number;
  graph?: {
    [k: string]: unknown;
  };
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
export interface OptionallyRequiredDate {
  relevant?: boolean;
  value?: string;
}
export interface PostUpdateModelRunInput {
  model_run_id: string;
  reason: string;
  record: ModelRunRecord;
}
export interface PostUpdateModelRunResponse {
  status: Status;
  session_id?: string;
}
export interface ProvenanceRecordInfo {
  id: string;
  prov_json: string;
  record: ModelRunRecord;
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
export interface StatusResponse {
  status: Status;
}
export interface SyncRegisterModelRunResponse {
  status: Status;
  record_info: ProvenanceRecordInfo;
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
