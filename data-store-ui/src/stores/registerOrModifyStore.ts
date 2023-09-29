import * as H from "history";
import lodashGet from "lodash.get";
import lodashSet from "lodash.set";
import { makeAutoObservable } from "mobx";
import { LabelPathAndValue } from "pages/UpdateMetadata";
import {
    DATA_STORE_API_ENDPOINTS,
    displayValidationError,
    requests,
} from "react-libs";
import { CollectionFormat } from "shared-interfaces/registryModels";
import { HTTPValidationError } from "../shared-interfaces/APIResponses";
import {
    MintResponse,
    RegistryFetchResponse,
    Schema,
    Status,
    UpdateMetadataResponse,
} from "../shared-interfaces/DataStoreAPI";

// Clean up function from
// https://stackoverflow.com/questions/23774231/how-do-i-remove-all-null-and-empty-string-values-from-an-object
const removeEmpty = (obj: any) => {
    Object.keys(obj).forEach(
        (k) =>
            (obj[k] && typeof obj[k] === "object" && removeEmpty(obj[k])) ||
            (!obj[k] && obj[k] !== undefined && delete obj[k])
    );
    return obj;
};

export class RegisterOrModifyStore {
    /*
    This class manages state for either the dataset registration 
    workflow and/or the dataset metadata update workflow.

    The reason for bundling this state is that they share a significant 
    mount of workflow methods and variations are minor (e.g. API endpoints.)

    Make sure to reset the store after completing a workflow.
    */

    // Is the schema loading?
    loading: boolean = false;

    // Is the schema finished loading and ready to go
    schemaReady: boolean = false;

    // Is there processing occurring (validation, registration or update)
    processing: boolean = false;

    // Message justifying processing - displayed in dialogue
    processingMessage?: string = undefined;

    // Error occurred?
    error: boolean = false;

    // Error message to display
    errorMessage?: string = undefined;

    // Possibly handle id - only defined for update workflow
    handle_id?: string = undefined;

    // The schema to fill out
    schema: JSON = {} as JSON;

    // The current value of the schema - controlled react component value
    // for rjsf library
    currentValue?: { [k: string]: unknown };

    constructor() {
        makeAutoObservable(this);
    }

    resetStore() {
        // Reset the store if navigating away
        // to ensure we don't carry state between instances
        this.loading = false;
        this.processing = false;
        this.processingMessage = undefined;
        this.error = false;
        this.errorMessage = undefined;
        this.handle_id = undefined;
        this.schema = {} as JSON;
        this.currentValue = undefined;
        this.schemaReady = false;
    }

    loadSchemaPromise() {
        // A generic helper used by both the update and mint
        // dataset workflows which returns a promise with the
        // successful result being the JSON schema object
        // and a failure response being the error message to
        // display.
        return new Promise((resolve, reject) => {
            requests
                .get(DATA_STORE_API_ENDPOINTS.METADATA_SCHEMA, {})
                .then((response) => {
                    let res = response as Schema;
                    // Workaround to get JSON format for schema
                    const schema = res.json_schema as unknown as JSON;
                    // Return value
                    resolve(schema);
                })
                .catch((e) => {
                    var errorMessage = "";
                    // Parse errors
                    if (e.response) {
                        errorMessage = `Failed to load schema! Response status code: ${
                            e.response.status
                        } and error detail: ${
                            e.response.data.detail ?? "Unknown"
                        }`;
                    } else if (e.message) {
                        errorMessage = `Failed to load schema! Response message: ${e.message}.`;
                    } else {
                        errorMessage =
                            "Failed to load schema! Unknown error occurred.";
                    }
                    reject(errorMessage);
                });
        });
    }
    loadSchemaFirstTime() {
        // Used when loading the schema for the dataset registration
        // workflow - i.e. when we don't have a handle for a preexisting
        // dataset
        this.loading = true;
        this.schemaReady = false;
        this.loadSchemaPromise()
            .then((rawSchema: any) => {
                this.schema = rawSchema as JSON;
                this.prepareDefaultValueFirstTime();
            })
            .catch((rawErrMsg: any) => {
                this.errorMessage = rawErrMsg as string;
                this.error = true;
                this.schemaReady = false;
            })
            .finally(() => {
                this.loading = false;
            });
    }

    prepareDefaultValueFirstTime() {
        // Injects default form values for new dataset workflow
        this.currentValue = {
            dataset_info: {
                access_info: {
                    reposited: true,
                },
            },
        };
        this.schemaReady = true;
    }

    loadSchemaExisting(handle_id: string) {
        // Used when loading the schema for the update dataset metadata
        // workflow - i.e. when we have a handle for a preexisting
        // dataset
        this.loading = true;
        this.schemaReady = false;
        this.handle_id = handle_id;
        this.loadSchemaPromise()
            .then((rawSchema: any) => {
                this.schema = rawSchema as JSON;
                this.prepareDefaultValueExisting(handle_id);
            })
            .catch((rawErrMsg: any) => {
                this.errorMessage = rawErrMsg as string;
                this.error = true;
                this.schemaReady = false;
            })
            .finally(() => {
                this.loading = false;
            });
    }

    prepareDefaultValueExisting(handle_id: string) {
        // When providing default, we should now use the
        // pulled registry item metadata
        requests
            .get(DATA_STORE_API_ENDPOINTS.FETCH_DATASET, {
                handle_id: handle_id,
            })
            .then((res) => {
                const response: RegistryFetchResponse =
                    res as RegistryFetchResponse;
                let fetchedMetadata = response.item?.collection_format;
                if (response.status.success) {
                    // Remove null fields from received to avoid
                    // bad input types
                    fetchedMetadata = removeEmpty(fetchedMetadata);
                    // Keep default value as raw form data - only useful in parsed format
                    // in the dataset detail view
                    this.currentValue = fetchedMetadata as unknown as {
                        [k: string]: unknown;
                    };
                    this.loading = false;
                    this.schemaReady = true;
                } else {
                    this.loading = false;
                    this.schemaReady = false;
                    this.error = true;
                    this.errorMessage = `Failed to fetch dataset! Error: ${
                        response.status.details ?? "Unspecified."
                    }`;
                }
            })
            .catch((e) => {
                this.error = true;
                this.loading = false;
                this.schemaReady = false;
                if (e.response) {
                    this.errorMessage = `Failed to fetch dataset! Response status code: ${
                        e.response.status
                    } and error detail: ${e.response.data.detail ?? "Unknown"}`;
                } else if (e.message) {
                    this.errorMessage = `Failed to fetch dataset! Response message: ${e.message}.`;
                } else {
                    this.errorMessage =
                        "Failed to fetch dataset! Unknown error occurred.";
                }
            });
    }

    registerNewDataset(inputData: CollectionFormat) {
        return new Promise((resolve, reject) => {
            // Calls the update metadata post
            // and interprets response including error conditions
            requests
                .post(
                    DATA_STORE_API_ENDPOINTS.MINT_DATASET,
                    inputData,
                    {},
                    {},
                    true
                )
                .then((response) => {
                    let res: MintResponse = response as MintResponse;
                    if (res.status.success) {
                        // Successful - redirecting to the dataset view
                        // with updated metadata
                        // Clean up state
                        resolve(res.handle);
                    } else {
                        // Something went wrong so handle error
                        const errorMessage = `Something went wrong when registering dataset: ${
                            res.status.details ??
                            "No error info provided. Contact administrator."
                        }`;
                        reject(errorMessage);
                    }
                })
                .catch((e) => {
                    var errorMessage: string = "";
                    if (e.response) {
                        if (e.response.status == 422) {
                            let valError: HTTPValidationError = e.response.data;
                            errorMessage =
                                "Validation errors: " +
                                displayValidationError(valError);
                        } else {
                            errorMessage = `Unexpected error when performing dataset registration, status code: ${
                                e.response.status
                            }, and reason: ${
                                e.response.data.detail ?? "Unknown"
                            }`;
                        }
                    } else if (e.message) {
                        errorMessage = `Unexpected error when performing dataset registration: ${e.message}. Contact administrator.`;
                    }
                    reject(errorMessage);
                });
        });
    }

    updateMetadata(inputData: CollectionFormat, reason: string) {
        return new Promise((resolve, reject) => {
            // Calls the update metadata post
            // and interprets response including error conditions
            requests
                .post(
                    `${DATA_STORE_API_ENDPOINTS.UPDATE_METADATA}?handle_id=${this.handle_id}`,
                    inputData,
                    { reason: reason },
                    {},
                    true
                )
                .then((response) => {
                    let res: UpdateMetadataResponse =
                        response as UpdateMetadataResponse;
                    if (res.status.success) {
                        // Successful - notify
                        resolve(true);
                    } else {
                        // Something went wrong so handle error
                        const errorMessage = `Something went wrong when updating metadata: ${
                            res.status.details ??
                            "No error info provided. Contact administrator."
                        }`;
                        reject(errorMessage);
                    }
                })
                .catch((e) => {
                    var errorMessage = "";
                    if (e.response) {
                        if (e.response.status == 422) {
                            let valError: HTTPValidationError = e.response.data;
                            errorMessage =
                                "Validation errors: " +
                                displayValidationError(valError);
                        } else {
                            errorMessage = `Unexpected error when performing metadata update, status code: ${
                                e.response.status
                            }, and reason: ${
                                e.response.data.detail ?? "Unknown"
                            }`;
                        }
                    } else if (e.message) {
                        errorMessage = `Unexpected error when performing metadata update: ${e.message}. Contact administrator.`;
                    }
                    reject(errorMessage);
                });
        });
    }

    validateMetadata(formData: JSON) {
        return new Promise((resolve, reject) => {
            // This method validates the metadata then performs an update
            // of the metadata
            var inputData: CollectionFormat | undefined = undefined;

            // Parse into proper input format
            try {
                inputData = formData as unknown as CollectionFormat;
            } catch (error: any) {
                const errorMessage = `Failed to convert form data into expected format, error: ${error.message}`;
                reject(errorMessage);
            }

            // Check if silly keyword handling
            // Json form data sends through list of null values rather
            // than not including
            let kwords = inputData!.dataset_info.keywords;
            if (kwords) {
                // Remove null or null like values
                kwords = kwords.filter((val) => !!val);
                if (kwords.length == 0) {
                    // Remove
                    inputData!.dataset_info.keywords = undefined;
                } else {
                    inputData!.dataset_info.keywords = kwords;
                }
            }

            requests
                .post(
                    DATA_STORE_API_ENDPOINTS.VALIDATE_METADATA,
                    inputData,
                    {},
                    true
                )
                .then((response) => {
                    let res: Status = response as Status;
                    if (res.success == true) {
                        resolve(inputData);
                    } else {
                        const errorMessage = `Failed to validate updated metadata, error details: ${
                            res.details ??
                            "No details provided. Contact administrator."
                        }`;
                        reject(errorMessage);
                    }
                })
                .catch((e) => {
                    var errorMessage;
                    console.log("Validation error");
                    console.log(e);
                    const response = e.response ?? e;
                    if (response) {
                        if (response.status == 422) {
                            console.log("422 found");
                            let valError: HTTPValidationError = response.data;
                            errorMessage =
                                "Validation error: " +
                                displayValidationError(valError);
                            console.log(errorMessage);
                        } else {
                            errorMessage = `Unexpected error when performing metadata validation, status code: ${
                                response.status
                            }, and reason: ${
                                response.data.detail ?? "Unknown"
                            }`;
                        }
                    } else if (e.message) {
                        errorMessage = `Unexpected error when performing metadata validation: ${e.message}. Contact administrator.`;
                    }
                    reject(errorMessage);
                });
        });
    }

    onFormChange(formData: JSON) {
        this.currentValue = formData as unknown as { [k: string]: unknown };
    }

    registerDatasetAction(formData: JSON, history: H.History) {
        // When submit we need to validate metadata and then
        // run the update metadata post
        this.processing = true;
        this.processingMessage = "Validating metadata ...";

        this.validateMetadata(formData)
            // Validate
            .then((rawCollectionFormat: any) => {
                let collectionFormat = rawCollectionFormat as CollectionFormat;
                this.processingMessage =
                    "Schema validation success. Registering dataset. Please wait...";
                return this.registerNewDataset(collectionFormat);
            })
            // Register
            .then((rawHandle: any) => {
                let handle = rawHandle as string;

                // Default view is upload tab
                const defaultView = "upload";
                var preferredView = defaultView;

                // But if not reposited, use the overview instead
                const reposited = (formData as unknown as { [k: string]: any })[
                    "dataset_info"
                ]["access_info"]["reposited"];
                if (reposited !== undefined && !reposited) {
                    preferredView = "overview";
                }
                this.resetStore();
                // Redirect to preferred view
                history.push(`/dataset/${handle}?view=${preferredView}`);
            })
            .catch((rawErrMessage: any) => {
                let errorMessage = rawErrMessage as string;
                this.processing = false;
                this.processingMessage = undefined;
                this.errorMessage = errorMessage;
                this.error = true;
            });
    }

    updateMetadataAction(formData: JSON, history: H.History, reason: string) {
        // When submit we need to validate metadata and then
        // run the update metadata post
        if (!this.handle_id) {
            this.processing = false;
            this.processingMessage = undefined;
            this.error = true;
            this.errorMessage =
                "Trying to update metadata without a valid handle id. Something went wrong - contact administrator.";
            return;
        }

        this.processing = true;
        this.processingMessage = "Validating metadata ...";

        this.validateMetadata(formData)
            // Validate
            .then((rawCollectionFormat: any) => {
                let collectionFormat = rawCollectionFormat as CollectionFormat;
                this.processingMessage =
                    "Schema validation success. Updating dataset. Please wait...";
                return this.updateMetadata(collectionFormat, reason);
            })
            // Update
            .then((_: any) => {
                // save handle before resetting
                const handle = this.handle_id;
                this.resetStore();
                history.push(`/dataset/${handle}?view=overview`);
            })
            .catch((rawErrMessage: any) => {
                let errorMessage = rawErrMessage as string;
                this.processing = false;
                this.processingMessage = undefined;
                this.errorMessage = errorMessage;
                this.error = true;
            });
    }

    closeErrorDialog() {
        this.error = false;
        this.errorMessage = undefined;
    }

    setLabelValue(labelValueSet: LabelPathAndValue[]) {
        if (this.currentValue !== undefined) {
            // Use lodash set to set this.currentValue values based on LabelPathAndValue pairs.
            labelValueSet.forEach((labelValuePair: LabelPathAndValue) => {
                lodashSet(
                    this.currentValue!,
                    labelValuePair.labelPath,
                    labelValuePair.value
                );
            });
        }
    }

    getLabelValue(labelPath: string): { status: boolean; value?: unknown } {
        if (this.currentValue === undefined) {
            // currentValue is undefined, return status is false.
            return { status: false, value: undefined };
        } else {
            // currentValue is not undefined, get label value
            const valueRes = lodashGet(this.currentValue, labelPath);
            return { status: true, value: valueRes };
        }
    }
}

export default new RegisterOrModifyStore();
