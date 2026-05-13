import {
    Alert,
    AlertTitle,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    Stack,
    Typography,
    MenuItem,
    FormControl,
    Select,
    InputLabel,
    SelectChangeEvent
} from "@mui/material";

import { useState, useEffect, useRef } from "react";
import { useGenerateReport } from "./useGenerateReport";
import { useJobMonitor } from "./useJobMonitor";
import { ItemSubType } from "../provena-interfaces/RegistryModels";
import { stripPossibleFullStop } from "../util";

export interface GenerateReportProps {
    id: string | undefined;
    itemSubType: ItemSubType | undefined;
}

// A literal list with set depth values.
const DEPTH_LIST = [1, 2, 3]

// Auto-retry configuration for cold-start failures
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 5000;

export const useGenerateReportDialog = (props: GenerateReportProps) => {

    const [popUpOpen, setPopupOpen] = useState<boolean>(false);
    const [depth, setDepth] = useState<number>(DEPTH_LIST[0]);
    const [sessionId, setSessionId] = useState<string | undefined>(undefined);
    const [reportUrl, setReportUrl] = useState<string | undefined>(undefined);
    const [retryCount, setRetryCount] = useState<number>(0);
    const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Call the react-query defined. 
    const { mutate, dataReady } = useGenerateReport({
        id: props.id,
        itemSubType: props.itemSubType,
        depth: depth
    })

    // Ref always pointing at the latest mutate object so retry timeouts avoid stale closures.
    const mutateRef = useRef(mutate);

    // Keep mutateRef current so the retry timeout always calls the latest mutate function.
    useEffect(() => {
        mutateRef.current = mutate;
    });

    // When the mutation errors, automatically retry up to MAX_RETRIES times.
    useEffect(() => {
        if (mutate?.isError && retryCount < MAX_RETRIES) {
            const timeoutId = setTimeout(() => {
                setRetryCount((prev: number) => prev + 1);
                mutateRef.current?.mutate(undefined, {
                    onSuccess: (res: any) => {
                        const sid = res?.session_id ?? res?.sessionId ?? undefined;
                        if (sid) {
                            setSessionId(sid);
                        }
                    }
                });
            }, RETRY_DELAY_MS);
            retryTimeoutRef.current = timeoutId;
            return () => {
                clearTimeout(timeoutId);
                retryTimeoutRef.current = null;
            };
        }
    }, [mutate?.isError, retryCount]);

    // Helper functions to open and close the popup. 
    const openDialog = () => {
        setPopupOpen(true);
    }

    const closeDialog = () => {
        // Clear state and close dialog
        setDepth(DEPTH_LIST[0])
        setPopupOpen(false);
        setSessionId(undefined);
        setReportUrl(undefined);
        setRetryCount(0);
        if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
            retryTimeoutRef.current = null;
        }
        if (dataReady) {
            // reset mutation
            mutate?.reset()
        }
    }

    const handleChange = (event: SelectChangeEvent) => {
        setDepth(parseInt(event.target.value))
    }

    const onSubmit = () => {
        // Validate that a depth has been chosen.
        if (depth !== null && dataReady) {
            // Cancel any pending auto-retry before a fresh manual submission
            if (retryTimeoutRef.current) {
                clearTimeout(retryTimeoutRef.current);
                retryTimeoutRef.current = null;
            }
            setRetryCount(0);
            // Proceed to submit... store session id on success so we can monitor
            mutate?.mutate(undefined, {
                onSuccess: (res: any) => {
                    const sid = res?.session_id ?? res?.sessionId ?? undefined;
                    if (sid) {
                        setSessionId(sid);
                    }
                }
            })
        }
    }

    // Submit button is disabled if depth is not picked.
    const submitDisabled = depth === null

    const monitor = useJobMonitor({
        sessionId: sessionId,
        showIO: true,
        refetchOnError: false,
        adminMode: false,
        onJobSuccess: (entry: any) => {
            const url = entry?.result?.report_url ?? entry?.result?.reportUrl;
            if (url) {
                // store the URL for explicit download by the user
                setReportUrl(url);
            }
        },
    });

    const renderedDialog = (
        <Dialog open={popUpOpen} onClose={closeDialog} fullWidth={true} maxWidth={"md"}>
            <DialogContent>
                <Stack spacing={2} gap={2} direction="column">

                    {mutate?.isError && retryCount < MAX_RETRIES && (
                        <Alert severity="warning" variant="outlined">
                            <AlertTitle>Retrying automatically</AlertTitle>
                            <Typography variant="subtitle1">
                                The report service may be starting up. Retrying automatically (attempt {retryCount + 1} of {MAX_RETRIES})...
                            </Typography>
                        </Alert>
                    )}

                    {mutate?.isError && retryCount >= MAX_RETRIES && (
                        <Alert severity="error" variant="outlined">
                            <AlertTitle>An error occurred</AlertTitle>
                            <Typography variant="subtitle1">
                                An error occurred while running the Generate Report operation. Error:{" "}
                                {mutate?.error
                                    ? stripPossibleFullStop(mutate?.error as string)
                                    : "Unknown. Try refreshing the page and performing the operation again, or contact an administrator for assistance."}
                            </Typography>
                        </Alert>
                    )}

                    {/* If we have a session id, render the job monitor view */}
                    {sessionId ? (
                        <div>{monitor.render()}</div>
                    ) : (
                        <>
                            <DialogContentText>
                                Generate a word document containing the associated inputs, model runs and outputs
                                originating from this {props.itemSubType} upto your chosen upstream depth and a fixed
                                downstream depth of 1.
                            </DialogContentText>
                            <FormControl fullWidth>
                                <InputLabel id="depth-select-label">Depth</InputLabel>
                                <Select
                                    labelId="depth-select-label"
                                    id="depth-simple-select"
                                    value={String(depth)}
                                    label="Depth"
                                    onChange={handleChange}

                                >
                                    {DEPTH_LIST.map((item: number) => (
                                        <MenuItem value={item} key={item}> {item}</MenuItem>
                                    ))}
                                </Select>
                                <Typography variant="caption" color="textSecondary">
                                    Select depth level for upstream exploration.
                                </Typography>
                            </FormControl>
                        </>
                    )}
                </Stack>
                <DialogActions>
                    <Button onClick={closeDialog}>{sessionId ? "Close" : "Cancel"}</Button>
                    {sessionId && (
                        <Button
                            color="primary"
                            disabled={!reportUrl}
                            onClick={() => {
                                if (reportUrl) {
                                    window.open(reportUrl, "_blank", "noopener,noreferrer");
                                }
                            }}
                        >
                            Download Report
                        </Button>
                    )}
                    {!sessionId && (
                        <Button color="success" disabled={submitDisabled} onClick={onSubmit}>
                            {mutate?.isLoading ? "Generating..." : "Generate Report"}
                        </Button>
                    )}
                </DialogActions>
            </DialogContent>
        </Dialog>
    )

    return {
        openDialog,
        closeDialog,
        renderedDialog
    }

}