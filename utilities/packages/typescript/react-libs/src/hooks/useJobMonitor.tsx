import {
    Button,
    CircularProgress,
    Divider,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import React, { useState } from "react";
import { GenericDetailViewWrapperComponent } from "../";
import { JobStatus, JobStatusTable } from "../shared-interfaces/AsyncJobAPI";
import { useJobSessionWatcher } from "./useJobSessionWatcher";

export const STATUS_COLOR_MAP: Map<JobStatus, string> = new Map([
    ["FAILED", "red"],
    ["SUCCEEDED", "green"],
    ["IN_PROGRESS", "blue"],
    ["PENDING", "blue"],
    ["DEQUEUED", "blue"],
]);

const statusToDescription = (status: JobStatus): string => {
    switch (status) {
        case "PENDING": {
            return "Your job has been created but is yet to start. Please wait a few moments. If the job fails to start, please contact us.";
        }
        case "DEQUEUED": {
            return "Your job has been removed from the queue by a worker.";
        }
        case "IN_PROGRESS": {
            return "Your job is in progress.";
        }
        case "SUCCEEDED": {
            return "Your job was successful.";
        }
        case "FAILED": {
            return "Your job failed! See the error info and contact us if you are unable to determine the cause of the error.";
        }
        default: {
            return "Please wait...";
        }
    }
};

interface AutoFetchingDisplayComponentProps {
    // default 13
    textSize?: number;
    // default 30
    loadingSize?: number;
}
export const AutoFetchingDisplayComponent = (
    props: AutoFetchingDisplayComponentProps
) => {
    /**
    Component: AutoFetchingDisplayComponent
    
    */
    return (
        <Stack direction="row" spacing={1} alignContent="center">
            <Typography
                variant="subtitle1"
                color="grey"
                style={{ fontSize: props.textSize ?? 13 }}
            >
                <b>Refetching</b>
            </Typography>
            <CircularProgress size={props.loadingSize ?? 30} />
        </Stack>
    );
};

interface JobStatusDisplayComponentProps {
    // Is the job status being currently auto refetched
    isAutoRefetching: boolean;
    entry: JobStatusTable;
    showIO: boolean;
    setInputExpanded: (expanded: boolean) => void;
    inputExpanded: boolean;
    setOutputExpanded: (expanded: boolean) => void;
    outputExpanded: boolean;
}
const JobStatusDisplayComponent = (props: JobStatusDisplayComponentProps) => {
    /**
    Component: JobStatusDisplayComponent

    Displays a JobStatusTable 
    */
    const entry = props.entry;

    return (
        <Stack spacing={4}>
            <Stack
                direction="row"
                justifyContent={"flex-start"}
                spacing={2}
                alignContent="center"
            >
                <Typography variant="h5">
                    Job <b>{entry.session_id}</b>
                </Typography>
                {props.isAutoRefetching && (
                    <AutoFetchingDisplayComponent textSize={20} />
                )}
            </Stack>
            <Grid
                container
                style={{ width: "100%" }}
                justifyContent={"space-between"}
            >
                <Grid item xs={6}>
                    <GenericDetailViewWrapperComponent
                        item={{
                            username: entry.username,
                            session_id: entry.session_id,
                            batch_id: entry.batch_id,
                            job_type: entry.job_type,
                            job_sub_type: entry.job_sub_type,
                            created_timestamp: entry.created_timestamp,
                        }}
                        layout="column"
                    />
                </Grid>
                <Grid item xs={6}>
                    <Stack>
                        <p>
                            Status:{" "}
                            <b
                                style={{
                                    color: STATUS_COLOR_MAP.get(entry.status),
                                }}
                            >
                                {entry.status}
                            </b>
                        </p>
                        <p>{statusToDescription(entry.status)}</p>
                        {entry.status === "FAILED" && (
                            <p>Error info: {entry.info ?? "None provided."}</p>
                        )}
                    </Stack>
                </Grid>
            </Grid>
            {props.showIO && (
                <React.Fragment>
                    <Stack direction="row" spacing={2}>
                        <Typography variant="h5">Input</Typography>
                        <Button
                            variant="outlined"
                            onClick={() => {
                                props.setInputExpanded(!props.inputExpanded);
                            }}
                        >
                            {props.inputExpanded ? "Collapse" : "Expand"}
                        </Button>
                    </Stack>
                    <Divider
                        orientation="horizontal"
                        style={{ width: "100%" }}
                    ></Divider>
                    {props.inputExpanded && (
                        <GenericDetailViewWrapperComponent
                            item={entry.payload}
                            layout="column"
                        />
                    )}
                    {entry.status === "SUCCEEDED" && (
                        <React.Fragment>
                            <Stack direction="row" spacing={2}>
                                <Typography variant="h5">Output</Typography>
                                <Button
                                    variant="outlined"
                                    onClick={() => {
                                        props.setOutputExpanded(
                                            !props.outputExpanded
                                        );
                                    }}
                                >
                                    {props.outputExpanded
                                        ? "Collapse"
                                        : "Expand"}
                                </Button>
                            </Stack>
                            {props.outputExpanded && (
                                <GenericDetailViewWrapperComponent
                                    item={entry.result ?? {}}
                                    layout="column"
                                />
                            )}
                        </React.Fragment>
                    )}
                </React.Fragment>
            )}
        </Stack>
    );
};

export interface UseJobMonitorProps {
    // If the session ID is defined, fetch and monitor it
    sessionId?: string;
    showIO: boolean;
    refetchOnError: boolean;
    onJobSuccess?: (entry: JobStatusTable) => void;
    adminMode: boolean;
}
export interface UseJobMonitorOutput {
    // The entry if it is available
    entry: JobStatusTable | undefined;
    render: () => JSX.Element | null;
}
export const useJobMonitor = (
    props: UseJobMonitorProps
): UseJobMonitorOutput => {
    /**
    Hook: useJobMonitor

    Uses the job session watcher to handle both the display and updating of a
    job. 
    */

    const [inputExpanded, setInputExpanded] = useState<boolean>(false);
    const [outputExpanded, setOutputExpanded] = useState<boolean>(false);

    const conditionalSuccessTrigger = (data: JobStatusTable) => {
        if (data.status === "SUCCEEDED") {
            if (props.onJobSuccess !== undefined) {
                props.onJobSuccess(data);
            }
        }
    };
    const monitor = useJobSessionWatcher({
        sessionId: props.sessionId,
        onSuccess: conditionalSuccessTrigger,
        refetchOnError: props.refetchOnError,
        adminMode: props.adminMode,
    });

    // Default render function
    var render: () => JSX.Element | null = () => {
        return null;
    };

    // Determine suitable render function based on status and API info
    if (monitor.loading && monitor.data === undefined) {
        render = () => {
            return (
                <Stack alignContent="center" style={{ width: "100%" }}>
                    <CircularProgress />
                </Stack>
            );
        };
    } else if (monitor.error) {
        render = () => {
            return (
                <div>
                    <Typography variant="subtitle1">
                        Please wait... retrieving job details
                    </Typography>
                    <Typography variant="body1">
                        Try waiting a few seconds. If the job does not load,
                        please contact us. Information:{" "}
                        {monitor.errorMessage ?? "No info provided."}
                    </Typography>
                </div>
            );
        };
    } else if (monitor.data !== undefined) {
        render = () => {
            return (
                <JobStatusDisplayComponent
                    isAutoRefetching={monitor.isAutoRefetching}
                    inputExpanded={inputExpanded}
                    setInputExpanded={setInputExpanded}
                    outputExpanded={outputExpanded}
                    setOutputExpanded={setOutputExpanded}
                    entry={monitor.data!}
                    showIO={props.showIO}
                ></JobStatusDisplayComponent>
            );
        };
    } else {
        render = () => {
            return null;
        };
    }

    return {
        entry: monitor.data,
        render,
    };
};
