import { action, makeAutoObservable } from "mobx";
import { DATA_STORE_API_ENDPOINTS, requests } from "react-libs";
import {
  CredentialResponse,
  CredentialsRequest,
} from "../provena-interfaces/DataStoreAPI";
import { ItemDataset } from "../provena-interfaces/RegistryAPI";
import { DatedCredentials } from "../types/types";

export class DatasetDetailStore {
  forceErrorBypass: boolean = false;
  requestingAwsCreds: boolean = false;
  requestingAWSCredsMessage: string | undefined;
  datasetDetail: ItemDataset | undefined = undefined;
  roles: string[] | undefined = undefined;
  locked: boolean | undefined = undefined;

  successfullyLodgedAccessChanges: boolean | undefined = undefined;
  accessUpdateLoading: boolean = false;
  accessUpdateError: boolean = false;
  accessUpdateErrorMessage: string | undefined = undefined;

  read_write_aws_creds: DatedCredentials | undefined = undefined;
  read_aws_creds: DatedCredentials | undefined = undefined;
  read_console_url: string | undefined = undefined;
  read_write_console_url: string | undefined = undefined;
  permission_metadata_read: boolean | undefined = undefined;
  permission_metadata_write: boolean | undefined = undefined;
  permission_data_read: boolean | undefined = undefined;
  permission_data_write: boolean | undefined = undefined;
  permission_admin: boolean | undefined = undefined;
  permission_loading: boolean = false;
  permission_error: boolean = false;
  permission_error_message: string | undefined = undefined;

  constructor() {
    makeAutoObservable(this);
  }

  resetStore() {
    this.forceErrorBypass = false;
    this.locked = false;
    this.requestingAwsCreds = false;
    this.requestingAWSCredsMessage = undefined;
    this.datasetDetail = undefined;
    this.roles = undefined;

    //this.accessConfig = undefined;
    //this.updatedAccessConfig = undefined;
    this.successfullyLodgedAccessChanges = undefined;
    this.accessUpdateLoading = false;
    this.accessUpdateError = false;
    this.accessUpdateErrorMessage = undefined;

    this.read_write_aws_creds = undefined;
    this.read_aws_creds = undefined;
    this.read_console_url = undefined;
    this.read_write_console_url = undefined;
    this.permission_metadata_read = undefined;
    this.permission_metadata_write = undefined;
    this.permission_data_read = undefined;
    this.permission_data_write = undefined;
    this.permission_admin = undefined;
    this.permission_loading = false;
    this.permission_error = false;
    this.permission_error_message = undefined;
  }

  dismissPermissionError() {
    this.forceErrorBypass = true;
    this.permission_error = false;
  }

  dismissAccessError() {
    this.accessUpdateLoading = false;
    this.accessUpdateError = false;
    this.accessUpdateErrorMessage = undefined;
    this.successfullyLodgedAccessChanges = false;
  }

  generateCreds(write: Boolean) {
    if (!this.datasetDetail || !this.datasetDetail.s3) {
      this.requestingAWSCredsMessage =
        "Cannot generate credentials when data details are undefined!";
      this.requestingAwsCreds = false;
    } else {
      this.requestingAwsCreds = true;
      this.requestingAWSCredsMessage = undefined;
      const credentialsRequest: CredentialsRequest = {
        dataset_id: this.datasetDetail.id,
        console_session_required: true,
      };
      requests
        .post(
          write
            ? DATA_STORE_API_ENDPOINTS.GENERATE_WRITE_CREDENTIALS
            : DATA_STORE_API_ENDPOINTS.GENERATE_READ_CREDENTIALS,
          credentialsRequest,
        )
        .then(
          action((response_json) => {
            const credResponse: CredentialResponse =
              response_json as CredentialResponse;
            if (!credResponse.status.success) {
              this.requestingAWSCredsMessage =
                "Status was failure on credential generation request, details: " +
                credResponse.status.details;
            } else {
              const creds = credResponse.credentials;
              const credsParsed: DatedCredentials = {
                aws_access_key_id: creds.aws_access_key_id,
                aws_secret_access_key: creds.aws_secret_access_key,
                aws_session_token: creds.aws_session_token,
                expiry: new Date(creds.expiry),
              };
              if (write) {
                this.read_write_aws_creds = credsParsed;
                this.read_write_console_url = credResponse.console_session_url;
              } else {
                this.read_aws_creds = credsParsed;
                this.read_console_url = credResponse.console_session_url;
              }
            }
          }),
        )
        .catch(
          action((reason) => {
            this.requestingAWSCredsMessage =
              "Something went wrong when generating credentials, Status code: " +
              reason.status +
              " with message: " +
              reason.data.detail;
          }),
        )
        .finally(action(() => (this.requestingAwsCreds = false)));
    }
  }
}

export default new DatasetDetailStore();
