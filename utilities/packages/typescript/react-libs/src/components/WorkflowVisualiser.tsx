import {
    CancelOutlined,
    CheckCircleOutline,
    KeyboardArrowDown,
    KeyboardArrowRight,
    PendingOutlined,
} from "@mui/icons-material";
import {
    Alert,
    AlertTitle,
    Button,
    Card,
    CircularProgress,
    Divider,
    Icon,
    IconButton,
    Paper,
    Stack,
    Theme,
    Tooltip,
    Typography,
} from "@mui/material";
import { createStyles, makeStyles, useTheme } from "@mui/styles";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import { JOB_DETAILS_ROUTE, SESSION_ID_QSTRING } from "../";
import {
    AutoFetchingDisplayComponent,
    ResolvedSessionInfo,
    WorkflowDefinition,
    WorkflowStep,
    useWorkflowManager,
} from "../hooks";
import { LoadedEntity } from "../interfaces";
import { GetJobResponse, JobStatus } from "../shared-interfaces/AsyncJobAPI";
import { GenericDetailViewWrapperComponent } from "./JsonRenderer";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            width: "100%",
            paddingBottom: theme.spacing(2),
        },
        title: {
            width: "100%",
            justifyContent: "space-between",
        },
        descriptionRow: {
            width: "100%",
            justifyContent: "space-between",
        },
        jobWrapper: {
            width: "100%",
            maxHeight: "80vh",
            overflowX: "auto",
            overflowY: "auto",
        },

        // Job component
        jobPaper: {
            width: "100%",
            padding: theme.spacing(1),
        },
        jobCard: {
            width: "100%",
            height: "100%",
            justifyContent: "space-between",
            padding: theme.spacing(1.5),
        },
        jobCardTopRow: {
            width: "100%",
            justifyContent: "space-between",
        },
        // other useful styles
        fullWidth: { width: "100%" },
    })
);

interface RenderJobEntryComponentProps {
    // Is the job status being currently auto refetched
    isAutoRefetching: boolean;
    job: LoadedEntity<GetJobResponse | undefined>;
    jobIndex: number;
    workflowStep: WorkflowStep;
    otherSessionInfo: Array<ResolvedSessionInfo>;
}
const RenderJobEntryComponent = (props: RenderJobEntryComponentProps) => {
    /**
    Component: RenderJobEntryComponent

    */
    const history = useHistory();
    const classes = useStyles();
    const theme = useTheme();

    const job = props.job;

    // Hover state
    const [hovered, setHovered] = useState<boolean>(false);

    // Fields for showing
    const stepName: string = props.workflowStep.name;
    const jobStatus: JobStatus | undefined = job.data?.job.status;
    const sessionId: string | undefined = job.data?.job.session_id;
    const createTimestamp: number | undefined = job.data?.job.created_timestamp;

    // Error
    const jobErrorAlert: JSX.Element = (
        <Alert
            variant="outlined"
            severity="error"
            className={classes.fullWidth}
        >
            <AlertTitle>Error: The job could not be retrieved</AlertTitle>
            Error: {job.errorMessage ?? "Unknown."}
        </Alert>
    );

    // Set item error message
    var errorMessage: string | undefined = undefined;
    var actionSuggestion: string | undefined = undefined;

    if (sessionId !== undefined) {
        errorMessage = props.otherSessionInfo[props.jobIndex]?.workflowError;
        actionSuggestion =
            props.otherSessionInfo[props.jobIndex]?.actionMessage;
    }

    // Set border colour based on job status
    // "PENDING" | "DEQUEUED" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED";
    const statusColour: string | undefined =
        jobStatus === "SUCCEEDED"
            ? theme.palette.success.main
            : jobStatus === "FAILED"
            ? theme.palette.error.main
            : jobStatus === "IN_PROGRESS"
            ? theme.palette.info.dark
            : jobStatus === "PENDING"
            ? theme.palette.info.light
            : jobStatus === "DEQUEUED"
            ? theme.palette.warning.light
            : theme.palette.background.default;

    return (
        <Paper className={classes.jobPaper} elevation={0}>
            <Card
                className={classes.jobCard}
                sx={{
                    border: `${hovered ? "3" : "1"}px solid ${statusColour}`,
                }}
                onClick={() => {
                    history.push(
                        `${JOB_DETAILS_ROUTE}?${SESSION_ID_QSTRING}=${sessionId}`
                    );
                }}
                onMouseEnter={() => {
                    setHovered(true);
                }}
                onMouseLeave={() => {
                    setHovered(false);
                }}
            >
                {job.error ? (
                    jobErrorAlert
                ) : (
                    <Stack direction="column" spacing={1.5}>
                        {/* Info for the top row */}
                        <Stack
                            direction="row"
                            className={classes.jobCardTopRow}
                        >
                            <Typography variant="h6">{stepName}</Typography>
                            {props.isAutoRefetching ? (
                                // If auto refetching - show constant loading
                                <AutoFetchingDisplayComponent />
                            ) : (
                                // If not auto refetching and loading
                                job.loading && <CircularProgress />
                            )}
                        </Stack>
                        {errorMessage ? (
                            <Alert
                                variant="outlined"
                                severity="error"
                                className={classes.fullWidth}
                            >
                                {errorMessage && (
                                    <Typography variant="body1">
                                        Error : {errorMessage}
                                    </Typography>
                                )}
                                {errorMessage && (
                                    <Typography variant="body1">
                                        Action suggested :{" "}
                                        {actionSuggestion ??
                                            "No action provided"}
                                    </Typography>
                                )}
                            </Alert>
                        ) : (
                            <GenericDetailViewWrapperComponent
                                item={{
                                    session_id: sessionId,
                                    status: jobStatus,
                                    created_timestamp: createTimestamp,
                                }}
                                layout="column"
                                key={sessionId}
                            ></GenericDetailViewWrapperComponent>
                        )}
                    </Stack>
                )}
            </Card>
        </Paper>
    );
};

export interface WorkflowVisualiserComponentProps {
    workflowDefinition: WorkflowDefinition;
    startingSessionID: string;
    // Only do row when there are only few steps and need a row view.
    direction?: "column" | "column-reverse" | "row" | "row-reverse" | undefined;
    // For component expand, will collapse things below workflow title bar
    enableExpand: boolean;
    // true for expanded at the start, false for collapsed at the start.
    defaultExpanded?: boolean;
    // Fetch in admin mode?
    adminMode: boolean;
}
export const WorkflowVisualiserComponent = (
    props: WorkflowVisualiserComponentProps
) => {
    /**
    Component: WorkflowVisualiserComponent

    Manages a workflow based on a definition and visualises the result 

    NOTE use the starting session ID as key to ensure remount under changing
    session ID
    */

    const classes = useStyles();

    const [expandedWorkflow, setExpandedWorkflow] = useState<boolean>(
        props.defaultExpanded ?? true
    );

    const workflow = useWorkflowManager({
        startingSessionId: props.startingSessionID,
        workflowDefinition: props.workflowDefinition,
        adminMode: props.adminMode,
    });

    // Handler
    const expandOnClick = () => {
        setExpandedWorkflow(!expandedWorkflow);
    };

    const refetchAll = () => {
        workflow.refetchAll();
    };

    return (
        <React.Fragment>
            <Stack direction="column" spacing={2} className={classes.root}>
                <Stack direction="row" spacing={2} className={classes.title}>
                    <Stack direction="row" spacing={2}>
                        <Typography variant="h6">
                            {props.workflowDefinition.name}
                        </Typography>
                        {workflow.success ? (
                            <Icon color="success">
                                <CheckCircleOutline />
                            </Icon>
                        ) : workflow.error ? (
                            <Icon color="error">
                                <CancelOutlined />
                            </Icon>
                        ) : (
                            <Icon color="info">
                                <Tooltip title="This workflow is in progress">
                                    <PendingOutlined />
                                </Tooltip>
                            </Icon>
                        )}
                    </Stack>
                    {props.enableExpand && (
                        <IconButton
                            aria-label="expand overflow visualiser"
                            size="small"
                            onClick={expandOnClick}
                        >
                            {expandedWorkflow ? (
                                <React.Fragment>
                                    <KeyboardArrowDown /> Collapse
                                </React.Fragment>
                            ) : (
                                <React.Fragment>
                                    <KeyboardArrowRight /> Expand
                                </React.Fragment>
                            )}
                        </IconButton>
                    )}
                </Stack>
                {expandedWorkflow && (
                    <Stack direction="column" spacing={2}>
                        <Divider />
                        <Stack
                            direction="row"
                            spacing={2}
                            className={classes.descriptionRow}
                            alignContent="center"
                        >
                            <Typography variant="body1">
                                {props.workflowDefinition.description}
                            </Typography>
                            <Button
                                disabled={!(workflow.success || workflow.error)}
                                onClick={refetchAll}
                                variant="outlined"
                                color="secondary"
                            >
                                Refresh
                            </Button>
                        </Stack>
                        {workflow.complete && workflow.error && (
                            <Alert variant="outlined" severity="error">
                                <AlertTitle>
                                    Error: Some jobs could not be fetched
                                </AlertTitle>
                                Error: Some jobs could not be fetched during the
                                workflow generation process.
                            </Alert>
                        )}
                        {!!workflow.workflowData && (
                            <Stack
                                direction={props.direction}
                                className={classes.jobWrapper}
                            >
                                {workflow.workflowData.map((data, index) => {
                                    return (
                                        <RenderJobEntryComponent
                                            isAutoRefetching={
                                                data.isAutoRefetching
                                            }
                                            job={data}
                                            jobIndex={index}
                                            workflowStep={
                                                props.workflowDefinition.steps[
                                                    index
                                                ]
                                            }
                                            otherSessionInfo={
                                                workflow.sessionInfo
                                            }
                                        />
                                    );
                                })}
                            </Stack>
                        )}
                    </Stack>
                )}
            </Stack>
        </React.Fragment>
    );
};
