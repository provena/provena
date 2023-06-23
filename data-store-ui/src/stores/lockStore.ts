import { action, makeAutoObservable } from "mobx";
import { StatusResponse } from "../shared-interfaces/DataStoreAPI";

class LockAction<T> {
    // Action status
    loading: boolean = false;
    error: boolean = false;
    succeeded: boolean = false;
    errorMessage: string | undefined = undefined;
    content: T | undefined = undefined;

    // Action promise
    getActionPromise: (
        request: () => Promise<any>,
        markSucceeded: () => void,
        setError: (error: boolean) => void,
        setLoading: (loading: boolean) => void,
        setErrorMessage: (message: string | undefined) => void,
        setContent: (content: T) => void
    ) => Promise<T>;

    constructor(
        action: (
            request: () => Promise<any>,
            markSucceeded: () => void,
            setError: (error: boolean) => void,
            setLoading: (loading: boolean) => void,
            setErrorMessage: (message: string | undefined) => void,
            setContent: (content: T) => void
        ) => Promise<T>
    ) {
        makeAutoObservable(this);
        this.getActionPromise = action;
    }

    // Reset the state
    runAction(request: () => Promise<any>) {
        return this.getActionPromise(
            // request action
            request,
            action(() => {
                this.succeeded = true;
            }),
            action((error: boolean) => {
                this.error = error;
            }),
            action((loading: boolean) => {
                this.loading = loading;
            }),
            action((errorMessage: string | undefined) => {
                this.errorMessage = errorMessage;
            }),
            action((content: T) => {
                this.content = content;
            })
        );
    }

    awaitingLoad() {
        // we shouldn't be loading, have an error, or have succeeded
        return !this.loading && !this.error && !this.succeeded;
    }

    ready() {
        // we shouldn't be loading, have an error, success should be marked and
        // content defined
        return (
            !this.loading &&
            !this.error &&
            this.content !== undefined &&
            this.succeeded
        );
    }

    reset() {
        this.loading = false;
        this.error = false;
        this.succeeded = false;
        this.errorMessage = undefined;
        this.content = undefined;
    }
}

function generateLockAction<T extends StatusResponse>(
    actionName: string
): LockAction<T> {
    return new LockAction<T>(
        (
            request: () => Promise<any>,
            markSucceeded: () => void,
            setError: (error: boolean) => void,
            setLoading: (loading: boolean) => void,
            setErrorMessage: (message: string | undefined) => void,
            setContent: (content: T) => void
        ) => {
            return new Promise((resolve, reject) => {
                setLoading(true);
                setError(false);
                setErrorMessage(undefined);

                // Run the specified request promise
                request()
                    .then((res) => {
                        let statusResponse = res as T;
                        if (statusResponse.status.success) {
                            // set the content
                            setContent(statusResponse);
                            // mark as success
                            markSucceeded();
                            // Respond with data
                            resolve(statusResponse);
                        } else {
                            reject(statusResponse.status.details);
                        }
                    })
                    .catch((e) => {
                        var errorMessage = "";
                        // Parse errors
                        if (e.response) {
                            errorMessage = `Failed to ${actionName}! Response status code: ${
                                e.response.status
                            } and error detail: ${
                                e.response.data.detail ?? "Unknown"
                            }`;
                        } else if (e.message) {
                            errorMessage = `Failed to ${actionName}! Response message: ${e.message}.`;
                        } else {
                            errorMessage = `Failed to ${actionName}! Unknown error occurred.`;
                        }
                        setError(true);
                        setErrorMessage(errorMessage);
                        reject(errorMessage);
                    })
                    .finally(() => {
                        setLoading(false);
                    });
            });
        }
    );
}
