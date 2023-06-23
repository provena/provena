import { useState } from "react";
import { ItemSubType } from "../shared-interfaces/RegistryModels";
import {
    Alert,
    AlertTitle,
    Button,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import { useRevertItem } from "./useRevertItem";
import { ItemRevertResponse } from "../shared-interfaces/RegistryAPI";
import { stripPossibleFullStop } from "../util/util";
import { DATA_STORE_LINK, REGISTRY_LINK } from "../queries/endpoints";

const nonRevertableEntityTypesDisplayMap: Map<
    ItemSubType,
    (id: string, version?: number) => JSX.Element
> = new Map([
    // This maps the item subtype to a message which can be directly displayed
    // in the popup dialog for reversion actions to redirect to the item in the
    // respective location (if possible).
    [
        "DATASET",
        (id: string, version?: number) => {
            const link = `${DATA_STORE_LINK}/dataset/${id}${
                version !== undefined ? "?version=" + version.toString() : ""
            }`;
            return (
                <p>
                    You cannot revert to a previous version of a dataset from
                    the registry. Instead, visit the item in the{" "}
                    <a href={link} target="_blank" rel="noreferrer">
                        Data Store
                    </a>
                    .
                </p>
            );
        },
    ],
    [
        "MODEL_RUN",
        (id: string) => {
            return (
                <p>
                    You cannot revert to a previous version of a model run. If
                    you would like to discuss options to help manage changes to
                    existing model runs, please contact us.
                </p>
            );
        },
    ],
]);

export type Context = "registry" | "data-store";
export interface UseRevertDialogProps {
    id?: string;
    historyId?: number;
    subtype?: ItemSubType;
    // Defaults to registry
    context?: Context;

    // Optional hook for when the revert is completed successfully
    onSuccess?: (response: ItemRevertResponse) => void;
}
export interface UseRevertDialogOutput {
    // Only available if data is provided
    startRevert?: () => void;
    // Renders the JSX element (dialog box)
    render: () => JSX.Element | null;
}
export const useRevertDialog = (
    props: UseRevertDialogProps
): UseRevertDialogOutput => {
    /**
    Hook: useRevertDialog
    
    Manages a dialog popup to submit a revert operation against a specified item ID and history ID.

    Asks the user for the reason as part of the popup and manages the lifecycle of the API event including success and error conditions.
    */
    // Is the popup active?
    const [popupOpen, setPopupOpen] = useState<boolean>(false);
    const [reason, setReason] = useState<string | undefined>(undefined);

    // On submit handler
    const onSubmit = () => {
        if (revertOp.dataReady) {
            if (revertOp.submit !== undefined) {
                revertOp.submit();
            }
        }
    };

    // Enter key handler
    const keyPressHandler = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            onSubmit();
        }
    };

    // Manage the revert API ops
    const revertOp = useRevertItem({
        id: props.id,
        historyId: props.historyId,
        reason: reason,
        subtype: props.subtype,
        onSuccess: (res) => {
            // Run the props on success if provided
            if (props.onSuccess !== undefined) {
                props.onSuccess(res);
            }
            // Always close the popup when succeeded
            setPopupOpen(false);
        },
    });

    // Default render option returns null - still safe to include in JSX
    var render: () => JSX.Element | null = () => {
        return null;
    };

    // Alternative states
    const loading = !!revertOp.response?.loading;
    const error = !!revertOp.response?.error;
    const errorMessage = revertOp.response?.errorMessage;

    // Determine if this is a special subtype which cannot be reverted from the
    // registry (currently datasets and model runs)
    var nonRevertableContent: JSX.Element | undefined = undefined;

    if ((props.context ?? ("registry" as Context)) === "registry") {
        if (
            props.subtype &&
            props.id &&
            nonRevertableEntityTypesDisplayMap.has(props.subtype)
        ) {
            // Use the ID to generate the JSX content
            nonRevertableContent = nonRevertableEntityTypesDisplayMap.get(
                props.subtype
            )!(props.id, props.historyId);
        }
    } else {
        // Data store
        if (props.subtype && props.id && props.subtype !== "DATASET") {
            nonRevertableContent = (
                <p>
                    You cannot revert to a previous version of a non dataset
                    from the data store. Instead, visit the item in the{" "}
                    <a href={REGISTRY_LINK} target="_blank" rel="noreferrer">
                        Registry
                    </a>
                    .
                </p>
            );
        }
    }

    const submitDisabled =
        nonRevertableContent !== undefined || !revertOp.dataReady || loading;

    if (popupOpen) {
        render = () => {
            return (
                <Dialog
                    open={popupOpen}
                    onClose={() => {
                        setPopupOpen(false);
                    }}
                    fullWidth={true}
                    maxWidth={"md"}
                >
                    <DialogTitle>Revert to previous version</DialogTitle>
                    <DialogContent>
                        {nonRevertableContent !== undefined ? (
                            nonRevertableContent
                        ) : (
                            <Stack spacing={2} direction="column">
                                <DialogContentText>
                                    Please provide a reason to revert to this
                                    previous version (v{props.historyId ?? "?"}
                                    ).
                                </DialogContentText>
                                <TextField
                                    value={reason}
                                    fullWidth
                                    disabled={loading}
                                    // Conditionally submits on enter key
                                    onKeyDown={keyPressHandler}
                                    onChange={(e) => {
                                        setReason(e.target.value);
                                    }}
                                    label="Enter your reason here..."
                                />
                                {loading && (
                                    <Stack
                                        direction="row"
                                        justifyContent="center"
                                    >
                                        <CircularProgress />
                                    </Stack>
                                )}
                                {error && (
                                    <Alert severity="error" variant="outlined">
                                        <AlertTitle>
                                            An error occurred
                                        </AlertTitle>
                                        <Typography variant="subtitle1">
                                            An error occurred while running the
                                            revert operation. Error:{" "}
                                            {errorMessage
                                                ? stripPossibleFullStop(
                                                      errorMessage
                                                  )
                                                : "Unknown"}
                                            . Try refreshing the page and
                                            performing the operation again, or
                                            contact an administrator for
                                            assistance.
                                        </Typography>
                                    </Alert>
                                )}
                            </Stack>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <Button
                            disabled={loading}
                            onClick={() => {
                                setPopupOpen(false);
                            }}
                        >
                            Cancel
                        </Button>
                        <Button
                            color="success"
                            disabled={submitDisabled}
                            onClick={onSubmit}
                        >
                            Submit
                        </Button>
                    </DialogActions>
                </Dialog>
            );
        };
    }
    return {
        render,
        startRevert: () => {
            // ensure the reason is not defined (e.g. from previous submit)
            setReason(undefined);
            setPopupOpen(true);
        },
    };
};
