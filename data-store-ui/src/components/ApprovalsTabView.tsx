import {
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Divider,
    Grid,
    Stack,
    Theme,
    Tooltip,
    Typography,
    useTheme,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useKeycloak } from "@react-keycloak/web";
import React, { useState } from "react";
import {
    DOCUMENTATION_BASE_URL,
    GenericDetailViewWrapperComponent,
    ReleaseActionText,
    ReleasedStatusText,
    RenderLongTextExpand,
    UseUserLinkServiceLookupOutput,
    releaseStateStylePicker,
    useUserLinkEnforcer,
    useUserLinkServiceLookup,
    userLinkEnforcerDocumentationLink,
    userLinkEnforcerProfileLink,
} from "react-libs";
import {
    ItemDataset,
    ReleaseAction,
    ReleaseHistoryEntry,
    ReleasedStatus,
} from "react-libs/shared-interfaces/RegistryAPI";
import { ApprovalsHistoryDialog } from "./ApprovalsHistoryDialog";
import HelpOutline from "@mui/icons-material/HelpOutline";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: { width: "100%" },
        detailsList: {},
        approvalStatusRow: {
            width: "100%",
            alignItems: "center",
        },
        actionButtons: {
            width: "100%",
        },
        // Other useful layout
        fullWidth: { width: "100%" },
        tbPaddings: {
            paddingTop: theme.spacing(2),
            paddingBottom: theme.spacing(2),
        },
    })
);

// Error alert messages

// User Link missing error message
const overrideMissingLinkMessage = (
    <p>
        You cannot take further actions on approvals without linking your user
        account to a registered Person in the Registry. For more information,
        visit{" "}
        <a
            href={userLinkEnforcerDocumentationLink}
            target="_blank"
            rel="noreferrer"
        >
            our documentation
        </a>
        . You can link your user account to a Person by visiting your{" "}
        <a href={userLinkEnforcerProfileLink} target="_blank" rel="noreferrer">
            user profile
        </a>
        .
    </p>
);

// Tooltip messages

// Submit for approval button disabled tooltip message
const submitForApprovalDisabledToolTipMessage: string =
    "This dataset has already been requested for approval. Further submissions for approval cannot be made at this time. Please wait for the approver to take action.";

// Take action for approval button disable tooltip message
const takeActionForApprovalDisabledToolTipMessage: string =
    "You have already responded to the approval request for the current dataset. Please await further requests from the requester";

interface ApprovalsTabViewProps {
    dataset: ItemDataset;
}

export const ApprovalsTabView = (props: ApprovalsTabViewProps) => {
    /**
    Component: ApprovalsTabView

    The main view for Approvals tab in dataset details
    */

    const classes = useStyles();
    const theme = useTheme();

    // Doc links
    const HELP_LINK = DOCUMENTATION_BASE_URL; // TODO, Link needs to be updated

    // If approvals history dialog need to open, true for opening, false for closing
    const [approvalsHistoryDialogOpen, setApprovalsHistoryDialogOpen] =
        useState<boolean>(false);

    // Get users info
    const { keycloak } = useKeycloak();

    // Get id from current user name
    const userLink: UseUserLinkServiceLookupOutput = useUserLinkServiceLookup({
        username: keycloak.tokenParsed?.preferred_username,
    });

    const userLinkedId = userLink.data;

    const datasetApproverId = props.dataset.release_approver;
    console.error(props.dataset);
    // user id link enforcer

    const linkEnforcer = useUserLinkEnforcer({
        blockEnabled: true,
        blockOnError: true,
        missingLinkMessage: overrideMissingLinkMessage,
    });

    // Set status and information for showing

    // If action taken, and is REJECT or APPROVE, then show action status,
    // otherwise show release status
    var approvalState: ReleasedStatus | ReleaseAction =
        "NOT_RELEASE" as ReleasedStatus;

    // Only show the latest requester/approver and their notes in the tab front page
    var requestedTime: number | undefined = undefined;
    var requester: string | undefined | null = undefined;
    var requesterNote: string = "";

    var approvalActionTime: number | undefined = undefined;
    var approver: string | undefined | null = undefined;
    var approverNote: string = "";

    // If there are some release history, update the latest information
    if (
        !!props.dataset.release_history &&
        props.dataset.release_history.length > 0
    ) {
        // Get the latest history info
        const releaseHistory: ReleaseHistoryEntry[] = JSON.parse(
            JSON.stringify(props.dataset.release_history)
        );
        const releaseHistoryLatestFirst = releaseHistory.reverse();
        const releaseHistoryLength = releaseHistory.length;

        // Get the latest requester info
        const latestRequesterInfo = releaseHistoryLatestFirst.find(
            (history: ReleaseHistoryEntry) =>
                history.action === ("REQUEST" as ReleaseAction)
        );

        if (!!latestRequesterInfo) {
            requester = latestRequesterInfo.requester;
            requesterNote =
                latestRequesterInfo.notes !== ""
                    ? latestRequesterInfo.notes
                    : "Requester note is not provided.";
            requestedTime = latestRequesterInfo.timestamp;
        }

        // Gest the latest approver info
        const latestApproverInfo = releaseHistoryLatestFirst.find(
            (history: ReleaseHistoryEntry) =>
                history.action === ("APPROVE" as ReleaseAction) ||
                history.action === ("REJECT" as ReleaseAction)
        );

        if (!!latestApproverInfo) {
            approver = latestApproverInfo.approver;
            approverNote =
                latestApproverInfo.notes !== ""
                    ? latestApproverInfo.notes
                    : "Approver note is not provided.";
            approvalActionTime = latestApproverInfo.timestamp;
        }

        // Update the latest approval status for showing on the tab
        approvalState =
            props.dataset.release_history[releaseHistoryLength - 1].action ===
            "REJECT"
                ? ("REJECT" as ReleaseAction)
                : props.dataset.release_history[releaseHistoryLength - 1]
                      .action === "APPROVE"
                ? ("APPROVE" as ReleaseAction)
                : props.dataset.release_status; // PENDING
    }

    // Dynamic Styles

    // Set colour for approval status
    const approvalStateColour: string =
        releaseStateStylePicker(approvalState).colour;

    // Set text for approval status
    const approvalStateText: ReleaseActionText | ReleasedStatusText =
        releaseStateStylePicker(approvalState).text;

    // Buttons disabled status

    // Submit for approval button disabled condition
    const submitForApprovalDisabled =
        !!props.dataset.release_status &&
        props.dataset.release_status !== ("NOT_RELEASED" as ReleasedStatus) &&
        approvalState !== ("REJECT" as ReleaseAction);

    // Take action for approval button disable condition
    const takeActionForApprovalDisabled =
        !!props.dataset.release_status &&
        props.dataset.release_status !== ("PENDING" as ReleasedStatus);

    // Don's show action buttons after dataset is approved, only leave the history button
    const hideActionButtons = approvalState === ("APPROVE" as ReleaseAction);

    // Don't show release history button if there is no release history for current dataset
    const hideJHistoryButton =
        !props.dataset.release_history ||
        props.dataset.release_history.length <= 0;

    // Handler
    const handleApprovalsHistoryOnClick = () => {
        setApprovalsHistoryDialogOpen(true);
    };

    // Status

    const userLinkLoading = userLink.loading;

    // User link missing
    const userLinkError = linkEnforcer.blocked;

    // Is current user the dataset's current approver?
    const isApprover =
        !!datasetApproverId &&
        !!userLinkedId &&
        !userLinkError &&
        datasetApproverId === userLinkedId;

    return (
        <React.Fragment>
            <Stack direction="column" className={classes.root} spacing={4}>
                {/* Details list */}
                <Stack
                    direction="column"
                    className={classes.detailsList}
                    spacing={4}
                    divider={<Divider orientation="horizontal" flexItem />}
                >
                    <Stack direction="column" spacing={4}>
                        {/* Approval status row */}{" "}
                        <Stack>
                            <Grid
                                container
                                className={classes.approvalStatusRow}
                            >
                                <Grid item xs={2}>
                                    <Typography variant="h6">
                                        Approval Status:{" "}
                                    </Typography>
                                </Grid>
                                <Grid item xs={2}>
                                    <Typography
                                        variant="body1"
                                        sx={{
                                            color: `${approvalStateColour}`,
                                        }}
                                    >
                                        <strong>{approvalStateText}</strong>
                                    </Typography>
                                </Grid>
                                <Grid
                                    item
                                    xs={8}
                                    className={classes.actionButtons}
                                >
                                    {/* Action buttons */}
                                    <Stack
                                        direction="row"
                                        spacing={1}
                                        justifyContent="flex-end"
                                    >
                                        {/* For current dataset's approver only */}
                                        {isApprover && !hideActionButtons && (
                                            <Tooltip
                                                title={
                                                    takeActionForApprovalDisabled
                                                        ? takeActionForApprovalDisabledToolTipMessage
                                                        : undefined
                                                }
                                            >
                                                <Box>
                                                    <Button
                                                        variant="contained"
                                                        disabled={
                                                            takeActionForApprovalDisabled ||
                                                            userLinkError
                                                        }
                                                        href={`/approval-action/${props.dataset.id}`}
                                                    >
                                                        Take Action for Approval
                                                    </Button>
                                                </Box>
                                            </Tooltip>
                                        )}
                                        {/* For all data admin, already checked before going into this tab */}
                                        {!hideActionButtons && (
                                            <Tooltip
                                                title={
                                                    submitForApprovalDisabled
                                                        ? submitForApprovalDisabledToolTipMessage
                                                        : undefined
                                                }
                                            >
                                                <Box>
                                                    <Button
                                                        variant="contained"
                                                        disabled={
                                                            submitForApprovalDisabled ||
                                                            userLinkError
                                                        }
                                                        href={`/approval-submission/${props.dataset.id}`}
                                                    >
                                                        Submit for Approval
                                                    </Button>
                                                </Box>
                                            </Tooltip>
                                        )}
                                        {/* For all approvals tab viewer, only show release history button when there is history */}
                                        {!hideJHistoryButton && (
                                            <Button
                                                variant="contained"
                                                disabled={userLinkError}
                                                onClick={
                                                    handleApprovalsHistoryOnClick
                                                }
                                            >
                                                Approvals History
                                            </Button>
                                        )}
                                        {/* Help Button */}
                                        <Button
                                            variant="contained"
                                            onClick={() => {
                                                window.open(
                                                    HELP_LINK,
                                                    "_blank",
                                                    "noopener,noreferrer"
                                                );
                                            }}
                                            endIcon={<HelpOutline />}
                                        >
                                            Help
                                        </Button>
                                        {/* Approvals history dialog */}
                                        {approvalsHistoryDialogOpen && (
                                            <ApprovalsHistoryDialog
                                                dialogOpen={
                                                    approvalsHistoryDialogOpen
                                                }
                                                setDialogOpen={
                                                    setApprovalsHistoryDialogOpen
                                                }
                                                dataset={props.dataset}
                                            />
                                        )}
                                    </Stack>
                                </Grid>
                            </Grid>
                        </Stack>
                        {/* Requested approver */}
                        {/* Only display when latest approver has been requested, but no approval action provided */}
                        {props.dataset.release_status ===
                            ("PENDING" as ReleasedStatus) &&
                            !!datasetApproverId && (
                                <Card
                                    sx={{
                                        border: "1px solid #0000ff",
                                        borderRadius: "8px",
                                    }}
                                >
                                    <CardContent>
                                        <Stack
                                            direction="column"
                                            className={classes.tbPaddings}
                                        >
                                            <Typography variant="h6">
                                                {`Awaiting approval action. Pending approver${
                                                    isApprover ? " (You):" : ":"
                                                }`}
                                            </Typography>
                                        </Stack>
                                        <Stack className={classes.tbPaddings}>
                                            <Typography variant="body1">
                                                <GenericDetailViewWrapperComponent
                                                    item={{
                                                        linked_person_id:
                                                            datasetApproverId,
                                                    }}
                                                    layout={"column"}
                                                />
                                            </Typography>
                                        </Stack>
                                    </CardContent>
                                </Card>
                            )}
                    </Stack>
                    {/* Requester info */}
                    {!!requester &&
                        !!approvalState &&
                        approvalState !== "NOT_RELEASED" && (
                            <Stack direction="column" spacing={4}>
                                <Stack direction="column" spacing={4}>
                                    <Typography variant="h6">
                                        Latest requester updates:{" "}
                                    </Typography>
                                    <GenericDetailViewWrapperComponent
                                        item={{
                                            created_timestamp: requestedTime,
                                        }}
                                        layout={"column"}
                                    />
                                    <GenericDetailViewWrapperComponent
                                        item={{
                                            linked_person_id: requester,
                                        }}
                                        layout={"column"}
                                    />
                                </Stack>
                                <Stack direction="column" spacing={4}>
                                    <Typography variant="h6">
                                        Requester Note:{" "}
                                    </Typography>
                                    <Typography variant="body1">
                                        <RenderLongTextExpand
                                            text={requesterNote}
                                            initialCharNum={500}
                                        />
                                    </Typography>
                                </Stack>
                            </Stack>
                        )}
                    {/* Approver info */}
                    {/* Only display when latest approver took some actions */}
                    {!!approver &&
                        props.dataset.release_status !==
                            ("PENDING" as ReleasedStatus) && (
                            <Stack direction="column" spacing={4}>
                                <Stack direction="column" spacing={4}>
                                    <Typography variant="h6">
                                        Latest approver updates:{" "}
                                    </Typography>
                                    <GenericDetailViewWrapperComponent
                                        item={{
                                            created_timestamp:
                                                approvalActionTime,
                                        }}
                                        layout={"column"}
                                    />
                                    <GenericDetailViewWrapperComponent
                                        item={{
                                            linked_person_id: approver,
                                        }}
                                        layout={"column"}
                                    />
                                </Stack>
                                <Stack direction="column" spacing={4}>
                                    <Typography variant="h6">
                                        Approver Note:{" "}
                                    </Typography>
                                    <Typography variant="body1">
                                        <RenderLongTextExpand
                                            text={approverNote}
                                            initialCharNum={500}
                                        />
                                    </Typography>
                                </Stack>
                            </Stack>
                        )}
                </Stack>
                {/* Loading */}
                {userLinkLoading && (
                    <Stack direction="row" className={classes.fullWidth}>
                        <CircularProgress />
                    </Stack>
                )}
                {/* Errors */}
                {userLinkError && (
                    <Stack direction="column" className={classes.fullWidth}>
                        {linkEnforcer.render}
                    </Stack>
                )}
            </Stack>
        </React.Fragment>
    );
};
