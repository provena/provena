import LaunchIcon from "@mui/icons-material/Launch";
import LockIcon from "@mui/icons-material/Lock";
import {
    Alert,
    AlertTitle,
    Backdrop,
    Box,
    Button,
    CircularProgress,
    Dialog,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    Stack,
    Tab,
    Tabs,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { useQuery } from "@tanstack/react-query";
import { CopyButton } from "components/CopyButton";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import {
    CopyFloatingButton,
    DOCUMENTATION_BASE_URL,
    DatasetAccess,
    JsonDetailViewWrapperComponent,
    LANDING_PAGE_LINK_PROFILE,
    MetadataHistory,
    ProvGraphTabView,
    REGISTRY_LINK,
    ReleaseActionText,
    ReleasedStatusText,
    RenderLongTextExpand,
    TabPanel,
    VersioningView,
    WorkflowDefinition,
    WorkflowVisualiserComponent,
    combineLoadStates,
    deriveDatasetAccess,
    fetchDataset,
    releaseStateStylePicker,
    timestampToLocalTime,
    useAccessCheck,
    useHistoricalDrivenItem,
    useMetadataHistorySelector,
    useQueryStringVariable,
    useRevertDialog,
} from "react-libs";
import { useWorkflowHelper } from "react-libs/hooks/useWorkflowHelper";
import { Link as RouteLink, useParams } from "react-router-dom";
import { datasetVersionIdLinkResolver } from "util/helper";
import BreadcrumbLinks from "../components/BreadcrumbLinks";
import {
    AWSCredentialDisplay,
    AuthorDetailsDisplayComponent,
    OrganisationDetailsDisplayComponent,
} from "../components/DatasetDisplayParts";
import { ItemRevertResponse } from "../shared-interfaces/RegistryAPI";
import datasetDetailStore from "../stores/datasetDetailStore";
import { DatedCredentials } from "../types/types";
import { ApprovalsTabView } from "components/ApprovalsTabView";
import {
    ItemDataset,
    ItemBase,
    ReleaseHistoryEntry,
    ReleaseAction,
} from "react-libs/shared-interfaces/RegistryAPI";
import { Credentials, ReleasedStatus } from "shared-interfaces/DataStoreAPI";
import { S3Explorer } from "components/S3Explorer";

const AWS_HELP_LINK_PRESIGNED =
    "https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexFlow: "column",
            minHeight: "60vh",
            backgroundColor: "white",
            marginBottom: theme.spacing(10),
            padding: theme.spacing(4),
            borderRadius: 5,
        },
        guidanceButton: {
            width: "90%",
            textAlign: "center",
        },
        button: {
            marginRight: theme.spacing(1),
        },
        "& h3": {
            marginBottom: 0,
        },
        dataset: {
            display: "flex",
            flexFlow: "row",
            padding: theme.spacing(2),
        },
        tabs: {
            marginTop: theme.spacing(2),
        },
        tabsRHContent: {
            margin: theme.spacing(0),
            paddingLeft: theme.spacing(6),
        },
        metadataOverview: {
            boxShadow: "0 0 2px 0 rgba( 31, 38, 135, 0.37 )",
            margin: theme.spacing(0),
            paddingTop: theme.spacing(0),
            paddingRight: theme.spacing(2),
            paddingLeft: theme.spacing(2),
            "& h4": {
                marginBottom: 0,
            },
        },
        overviewGrid: {
            margin: theme.spacing(0),
            paddingTop: theme.spacing(0),
            paddingRight: theme.spacing(2),
            paddingBottom: theme.spacing(4),
        },
        panelContext: {
            "& h4": {
                marginBottom: 0,
            },
        },
        code: {
            backgroundColor: theme.palette.grey[300],
            padding: theme.spacing(2),
            wordWrap: "break-word",
        },
        fullWidth: {
            width: "100%",
        },
    })
);

interface DatasetApprovalsComponentProps {
    dataset: ItemDataset;
}
const DatasetApprovalsComponent = (props: DatasetApprovalsComponentProps) => {
    /**
    Component: DatasetApprovalsComponent

    Displays the dataset approvals status
    
    */
    const approvals = props.dataset.collection_format.approvals;

    return (
        <div>
            <h2>Dataset Approvals</h2>
            <h3>Ethics and privacy for dataset registration:</h3>
            Relevant:{" "}
            <i>{approvals.ethics_registration.relevant ? "Yes" : "No"}</i>
            <br />
            Obtained:{" "}
            <i>{approvals.ethics_registration.obtained ? "Yes" : "No"}</i>
            <h3>Ethics and privacy for dataset access:</h3>
            Relevant: <i>{approvals.ethics_access.relevant ? "Yes" : "No"}</i>
            <br />
            Obtained: <i>{approvals.ethics_access.obtained ? "Yes" : "No"}</i>
            <h3>Indigenous Knowledge:</h3>
            {approvals.indigenous_knowledge.relevant
                ? approvals.indigenous_knowledge.obtained
                    ? "Contains approved Indigenous knowledge."
                    : "Contains Indigenous knowledge - consent pending."
                : "NA"}
            <h3>Export Sensitive Data:</h3>
            {approvals.export_controls.relevant
                ? approvals.export_controls.obtained
                    ? "Contains approved export sensitive data."
                    : "Contains export sensitive data - consent pending."
                : "NA"}
        </div>
    );
};

// Workflow visualiser render
interface WorkflowViewComponentProps {
    startingSessionId: string;
    workflowDefinition: WorkflowDefinition;
    defaultExpanded?: boolean;
    adminMode: boolean;
}

const WorkflowViewComponent = (
    props: WorkflowViewComponentProps
): JSX.Element => {
    return (
        <Box paddingTop={8}>
            <WorkflowVisualiserComponent
                startingSessionID={props.startingSessionId}
                workflowDefinition={props.workflowDefinition}
                key={props.startingSessionId}
                direction="column"
                enableExpand={true}
                defaultExpanded={props.defaultExpanded}
                adminMode={props.adminMode}
            />
        </Box>
    );
};

type PreviewProps = {
    dataset: ItemDataset;
};

const PreviewDataset = observer((props: PreviewProps) => {
    const classes = useStyles();

    const collectionFormat = props.dataset.collection_format;

    // Establish keyword list
    var keywordList = undefined;
    let kwords = collectionFormat.dataset_info.keywords;
    if (kwords && kwords.length > 0) {
        keywordList = kwords.map((word: string) => {
            return (
                <li key={word}>
                    <b>{word}</b>
                </li>
            );
        });
    }

    // Initial character numbers for long dataset description.
    const descriptionInitialCharNum = 200;

    // Approval status and related colour

    // Default values for no release history
    var approvalStateColour: string = "inherit";
    var approvalStateText: ReleaseActionText | ReleasedStatusText =
        "NOT RELEASED";

    // get latest history first if has release history
    if (
        !!props.dataset.release_history &&
        props.dataset.release_history.length > 0
    ) {
        const releaseHistoryCopy: ReleaseHistoryEntry[] = JSON.parse(
            JSON.stringify(props.dataset.release_history)
        ) as ReleaseHistoryEntry[];

        const latestFirstReleaseHistory = releaseHistoryCopy.reverse();
        const approvalState =
            latestFirstReleaseHistory[0].action === "REJECT"
                ? ("REJECT" as ReleaseAction)
                : latestFirstReleaseHistory[0].action === "APPROVE"
                ? ("APPROVE" as ReleaseAction)
                : props.dataset.release_status;

        // Update Styles
        // Set colour for approval status
        approvalStateColour = releaseStateStylePicker(approvalState).colour;
        // Set text for approval status
        approvalStateText = releaseStateStylePicker(approvalState).text;
    }

    // Present data back to user
    return (
        <React.Fragment>
            <Grid container>
                {/* row 1 */}
                <Grid item xs={6}>
                    <h2>Dataset Information</h2>
                </Grid>
                <Grid item xs={6}>
                    <h2>Author Information</h2>
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <h3>Dataset name:</h3>
                    {props.dataset.collection_format.dataset_info.name}
                    <h3>Dataset description:</h3>
                    <RenderLongTextExpand
                        text={
                            props.dataset.collection_format.dataset_info
                                .description
                        }
                        initialCharNum={descriptionInitialCharNum}
                    />
                    <h3>Date created:</h3>
                    {collectionFormat.dataset_info.created_date}
                    <h3>Approval status:</h3>
                    <Typography sx={{ color: approvalStateColour }}>
                        {approvalStateText}
                    </Typography>
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <AuthorDetailsDisplayComponent
                        username={props.dataset.owner_username}
                    />
                </Grid>
                {/* row 2 */}
                <Grid item xs={6}>
                    <h2>Author Organisation Information</h2>
                </Grid>
                <Grid item xs={6}>
                    <h2>Publisher Information</h2>
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <OrganisationDetailsDisplayComponent
                        organisationId={
                            props.dataset.collection_format.associations
                                .organisation_id
                        }
                        // title={"Author Organisation Information"}
                    />
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <OrganisationDetailsDisplayComponent
                        organisationId={
                            props.dataset.collection_format.dataset_info
                                .publisher_id
                        }
                        // title={"Publisher Information"}
                    />
                </Grid>
                {/* row 3 */}
                <Grid item xs={6}>
                    <h2>License</h2>
                </Grid>
                <Grid item xs={6}>
                    <h2>Keywords</h2>
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <h3>URL</h3>
                    <a
                        href={collectionFormat.dataset_info.license}
                        target="_blank"
                    >
                        {collectionFormat.dataset_info.license}
                    </a>
                </Grid>
                <Grid item xs={6} className={classes.overviewGrid}>
                    <h3></h3>
                    {keywordList ? <ul>{keywordList}</ul> : "No keywords."}
                </Grid>
            </Grid>
        </React.Fragment>
    );
});

interface DatasetDetailsComponentProps {
    dataset: ItemBase;
}

const DatasetDetailsComponent = (props: DatasetDetailsComponentProps) => {
    /**
    * Component: DatasetDetailsComponent

    * This component renders the Details tab content
    */
    return props.dataset ? (
        <div style={{ width: "inherit" }}>
            <h2>Dataset Details</h2>
            <Stack direction="column" spacing={1}>
                <JsonDetailViewWrapperComponent
                    item={props.dataset}
                    layout={"column"}
                />
            </Stack>
        </div>
    ) : (
        <Grid>
            <CircularProgress />
        </Grid>
    );
};

interface LineageGraphComponentProps {
    rootID: string;
}

const LineageGraphComponent = (props: LineageGraphComponentProps) => {
    /**
    * Component: LineageGraphComponent

    * This component renders ProveGraph
    */
    return props.rootID ? (
        <div style={{ width: "inherit" }}>
            <h2>Lineage Graph</h2>
            <ProvGraphTabView rootID={props.rootID} />
        </div>
    ) : (
        <Grid>
            <CircularProgress />
        </Grid>
    );
};

interface VersioningViewComponentProps {
    item: ItemBase;
    isAdmin: boolean;
}

const VersioningViewComponent = (props: VersioningViewComponentProps) => {
    /**
    * Component: VersioningViewComponent

    * This component renders Versioning tab
    */

    return (
        <Stack direction="column" sx={{ width: "inherit" }} rowGap={2}>
            <h2>Dataset Versioning</h2>
            <VersioningView
                item={props.item}
                isAdmin={props.isAdmin}
                showSubtypeHeaderComponent={false}
                versionIdLinkResolver={datasetVersionIdLinkResolver}
            />
        </Stack>
    );
};

interface CredentialRequestProps {
    consoleURL: string | undefined;
    creds: DatedCredentials | undefined;
    loading: boolean;
    errorMessage: string | undefined;
    requestNewCreds: () => void;
}

const CredentialRequest = observer((props: CredentialRequestProps) => {
    /**
    * Component: CredentialRequest

    * This component renders the status of the credential request, 
    * a refresh button, and the expiry of the credentials.
    */
    if (props.loading) {
        return (
            <div>
                <Grid container>
                    <Grid
                        item
                        container
                        justifyContent="center"
                        alignItems="center"
                        spacing={2}
                    >
                        <Grid item xs="auto">
                            Please wait, your credentials are loading...
                        </Grid>
                        <Grid item xs="auto">
                            <CircularProgress />
                        </Grid>
                    </Grid>
                </Grid>
            </div>
        );
    } else if (props.errorMessage) {
        return (
            <div>
                <Grid container>
                    <Grid
                        item
                        container
                        justifyContent="center"
                        alignItems="center"
                        spacing={2}
                    >
                        <Grid item>
                            An error occurred when retrieving your credentials.
                            Error message: {props.errorMessage}. You can try
                            requesting credentials again by clicking the request
                            button.
                        </Grid>
                        <Grid item xs="auto">
                            <Button
                                onClick={props.requestNewCreds}
                                variant="contained"
                            >
                                Request credentials
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
            </div>
        );
    } else if (props.creds) {
        return (
            <div>
                <Grid container>
                    <Grid
                        item
                        container
                        justifyContent="center"
                        alignItems="center"
                        spacing={2}
                    >
                        <Grid item xs="auto">
                            Expiry: {"" + props.creds.expiry}
                        </Grid>
                        <Grid item xs="auto">
                            <Button
                                variant="contained"
                                onClick={props.requestNewCreds}
                            >
                                Refresh credentials
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
            </div>
        );
    } else {
        return (
            <div>
                <Grid container>
                    <Grid
                        item
                        container
                        justifyContent="center"
                        alignItems="center"
                        spacing={2}
                    >
                        <Grid item xs="auto">
                            No credentials generated, click here to request
                        </Grid>
                        <Grid item xs="auto">
                            <Button
                                onClick={props.requestNewCreds}
                                variant="contained"
                            >
                                Request credentials
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
            </div>
        );
    }
});

const fullLockGuidance = () => {
    const lockGuidanceLink =
        DOCUMENTATION_BASE_URL + "/registry/resource_lock.html";
    return (
        <Stack
            justifyContent="center"
            padding={2}
            spacing={2}
            divider={<Divider orientation="horizontal" flexItem />}
        >
            <Grid
                container
                justifyContent={"center"}
                spacing={3}
                alignItems="center"
            >
                <Grid item>This dataset is locked</Grid>
                <Grid item>
                    <LockIcon fontSize={"large"} />
                </Grid>
            </Grid>
            <p style={{ textAlign: "center" }}>
                This dataset has been locked. You cannot modify this dataset
                unless it is unlocked. Click{" "}
                <a href={lockGuidanceLink} target="_blank">
                    here
                </a>{" "}
                to learn more.
            </p>
        </Stack>
    );
};
const shortLockGuidance = (
    <Grid
        container
        xs={12}
        justifyContent={"center"}
        spacing={3}
        alignItems="center"
    >
        <Grid item>This dataset is locked</Grid>
        <Grid item>
            <LockIcon fontSize={"large"} />
        </Grid>
    </Grid>
);

// Release upload lock guidance

// Released
const releaseApprovedLockGuidance = () => {
    // TODO, Link needs to be updated
    const releaseApprovedLockGuidanceLink =
        DOCUMENTATION_BASE_URL + "/registry/resource_lock.html";
    return (
        <Stack
            justifyContent="center"
            padding={2}
            spacing={2}
            divider={<Divider orientation="horizontal" flexItem />}
        >
            <Grid
                container
                justifyContent={"center"}
                spacing={3}
                alignItems="center"
            >
                <Grid item>This dataset is locked</Grid>
                <Grid item>
                    <LockIcon fontSize={"large"} />
                </Grid>
            </Grid>
            <p style={{ textAlign: "center" }}>
                This dataset has been approved and cannot be modified. Click{" "}
                <a href={releaseApprovedLockGuidanceLink} target="_blank">
                    here
                </a>{" "}
                to learn more.
            </p>
        </Stack>
    );
};

// Pending
const releasePendingLockGuidance = () => {
    // TODO, Link needs to be updated
    const releasePendingLockGuidanceLink =
        DOCUMENTATION_BASE_URL + "/registry/resource_lock.html";
    return (
        <Stack
            justifyContent="center"
            padding={2}
            spacing={2}
            divider={<Divider orientation="horizontal" flexItem />}
        >
            <Grid
                container
                justifyContent={"center"}
                spacing={3}
                alignItems="center"
            >
                <Grid item>This dataset is locked</Grid>
                <Grid item>
                    <LockIcon fontSize={"large"} />
                </Grid>
            </Grid>
            <p style={{ textAlign: "center" }}>
                This dataset is being reviewed and cannot be modified. Click{" "}
                <a href={releasePendingLockGuidanceLink} target="_blank">
                    here
                </a>{" "}
                to learn more.
            </p>
        </Stack>
    );
};

type DownloadGuidanceProps = {
    dataset: ItemDataset;
};

const DownloadGuidance = observer((props: DownloadGuidanceProps) => {
    const classes = useStyles();
    const cliGuidanceLink =
        DOCUMENTATION_BASE_URL + "/data-store/downloading-datasets.html";
    const downloadingGuidanceLink =
        DOCUMENTATION_BASE_URL +
        "/data-store/downloading-datasets.html#downloading-and-synchronising-datasets";
    const creds = datasetDetailStore.read_aws_creds;
    const consoleURL = datasetDetailStore.read_console_url;
    // Defaults to not external - test if external
    const isExternal = !(
        props.dataset.collection_format.dataset_info.access_info.reposited ??
        true
    );

    return (
        <div>
            <h2>Download Dataset Files</h2>
            {isExternal && (
                <div style={{ marginBottom: "20px" }}>
                    <Alert variant="outlined" severity="warning">
                        <AlertTitle>Externally Reposited Data</AlertTitle>
                        This dataset has been marked as having files stored
                        externally. You may still use the provided storage to
                        host attachments or other data associated with the
                        primary dataset files.
                    </Alert>
                </div>
            )}
            <div>
                You can download files from this dataset using the methods
                below. For more information visit{" "}
                <a href={downloadingGuidanceLink} target="_blank">
                    this link.
                </a>{" "}
                Start by requesting credentials using the button below.
            </div>
            <h3>Credentials</h3>
            <CredentialRequest
                consoleURL={consoleURL}
                creds={creds}
                loading={datasetDetailStore.requestingAwsCreds}
                errorMessage={datasetDetailStore.requestingAWSCredsMessage}
                requestNewCreds={() => datasetDetailStore.generateCreds(false)}
            ></CredentialRequest>
            {creds ? (
                <React.Fragment>
                    <Grid container rowGap={2}>
                        <Grid item xs={12}>
                            <h3>
                                Previewing and downloading files individually
                            </h3>
                        </Grid>
                        <Grid item xs={12}>
                            <div
                                style={{ width: "100%", marginBottom: "10px" }}
                            >
                                Using the previewer below, you can navigate the
                                files in this dataset, generate{" "}
                                <a
                                    href={AWS_HELP_LINK_PRESIGNED}
                                    target="_blank"
                                    referrerPolicy="no-referrer"
                                >
                                    Presigned URLs
                                </a>
                                , and copy file paths.
                            </div>
                            <S3Explorer
                                datasetId={props.dataset.id}
                                bucket={props.dataset.s3.bucket_name}
                                credentials={
                                    {
                                        ...creds,
                                        expiry: creds.expiry.toString(),
                                    } as Credentials
                                }
                                prefix={props.dataset.s3.path}
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <Grid container justifyContent="space-between">
                                <Grid item xs={7.5}>
                                    <div>
                                        The below method allows you to explore
                                        the dataset with a GUI and download
                                        files individually:
                                    </div>
                                    <ol>
                                        <li>
                                            Open{" "}
                                            <a
                                                href={consoleURL}
                                                target="_blank"
                                            >
                                                this link
                                            </a>{" "}
                                            or the button on the right to login
                                            to the AWS system. You will be
                                            brought to your storage location
                                            automatically.
                                        </li>
                                        <li>
                                            You can now explore the dataset and
                                            use the orange 'Download' action
                                            after ticking an item.
                                        </li>
                                    </ol>
                                </Grid>
                                <Grid item xs={3.5}>
                                    <Stack
                                        direction="column"
                                        justifyContent="space-evenly"
                                        alignItems="stretch"
                                        style={{ height: "100%" }}
                                    >
                                        <Button
                                            className={classes.guidanceButton}
                                            variant="contained"
                                            onClick={() => {
                                                window.open(
                                                    consoleURL,
                                                    "_blank"
                                                );
                                            }}
                                        >
                                            Click to open storage location
                                        </Button>
                                        <Button
                                            className={classes.guidanceButton}
                                            variant="contained"
                                            onClick={() => {
                                                window.open(
                                                    downloadingGuidanceLink,
                                                    "_blank"
                                                );
                                            }}
                                        >
                                            Click to learn more
                                        </Button>
                                    </Stack>
                                </Grid>
                            </Grid>
                        </Grid>
                    </Grid>

                    <h3>Downloading the whole dataset</h3>
                    <div>
                        To download all the files of a dataset, you need to use
                        the AWS CLI. The steps below will give guidance on this
                        process.
                    </div>
                    <div>
                        Please note that you need to have the AWS CLI v2
                        installed to follow the below steps. For more
                        information on how to prepare your system for CLI upload
                        (and download), visit{" "}
                        <a href={cliGuidanceLink} target="_blank">
                            this guide
                        </a>
                        .
                    </div>
                    <ol>
                        <li>
                            Shown below are your temporary <b>read-only</b> AWS
                            programmatic access credentials:
                            <AWSCredentialDisplay
                                credentials={creds}
                            ></AWSCredentialDisplay>
                        </li>
                        <li>
                            Copy and paste the credentials into your AWS CLI
                            terminal environment. You can change the format of
                            the environment variable export statements using the
                            buttons above the generated credentials.
                        </li>
                        <li>
                            Using your terminal, navigate to where you want the
                            data to be downloaded to. You should create a new
                            folder to put the dataset files into. Use the below
                            command to copy all files from the dataset into your
                            folder, replacing 'folder' with the name of your
                            folder:
                            <div className={classes.code}>
                                <CopyFloatingButton
                                    clipboardText={`aws s3 cp ${props.dataset.s3.s3_uri} folder --recursive`}
                                />
                                aws s3 cp {props.dataset.s3.s3_uri} folder
                                --recursive
                            </div>
                        </li>
                        <li>
                            You can use other AWS CLI commands to explore the
                            directory, including the list command:
                            <div className={classes.code}>
                                <CopyFloatingButton
                                    clipboardText={`aws s3 ls ${props.dataset.s3.s3_uri}`}
                                />
                                aws s3 ls {props.dataset.s3.s3_uri}
                            </div>
                            Or by using the AWS console to preview your bucket
                            location's contents (see links in above method).
                        </li>
                    </ol>
                </React.Fragment>
            ) : null}
        </div>
    );
});

type ExternalAccessProps = {
    dataset: ItemDataset;
};

const ExternalAccess = observer((props: ExternalAccessProps) => {
    /**
    Provides a summary of information about external dataset access. 
    This applies for datasets which are not reposited in the data store.
     */
    const documentationLink =
        DOCUMENTATION_BASE_URL + "/data-store/externally-hosted-datasets.html";
    const accessInfo = props.dataset.collection_format.dataset_info.access_info;
    const isWebUrl = (accessInfo.uri ?? "Unknown").startsWith("http");

    return (
        <div>
            <h2>External Access Information</h2>
            <p>
                This dataset references files which are hosted externally. The
                dataset files are not available for download through the Data
                Store. You may be able to access the dataset files based on the
                information provided below. For more information, visit{" "}
                <a href={documentationLink} target="_blank" rel="noreferrer">
                    our documentation
                </a>
                .
            </p>
            <div>
                <h3>External access URI:</h3>
                {isWebUrl ? (
                    <a
                        href={accessInfo.uri ?? ""}
                        target="_blank"
                        rel="noreferrer"
                    >
                        {accessInfo.uri ?? "Not provided - contact admin"}
                    </a>
                ) : (
                    accessInfo.uri ?? "Not provided - contact admin"
                )}
                <CopyFloatingButton
                    clipboardText={accessInfo.uri ?? ""}
                    iconOnly={true}
                    withConfirmationText={true}
                />
            </div>
            <div>
                <h3>More information:</h3>
                {accessInfo.description ?? "Not provided - contact admin."}
            </div>
        </div>
    );
});

type UploadGuidanceProps = {
    dataset: ItemDataset;
    locked: boolean;
    writeAccess: boolean;
};

const UploadGuidance = observer((props: UploadGuidanceProps) => {
    const classes = useStyles();
    const cli_guidance_link =
        DOCUMENTATION_BASE_URL + "/data-store/setting-up-the-aws-cli.html";
    const registering_guidance_link =
        DOCUMENTATION_BASE_URL + "/data-store/registering-a-dataset.html";
    const guiUploadingGuidanceLink =
        DOCUMENTATION_BASE_URL + "/data-store/uploading-dataset-files.html";
    const creds = datasetDetailStore.read_write_aws_creds;
    const consoleURL = datasetDetailStore.read_write_console_url;
    // Defaults to not external - test if external
    const isExternal = !(
        props.dataset.collection_format.dataset_info.access_info.reposited ??
        true
    );

    if (props.locked) {
        return (
            <div>
                <h2>Upload Dataset Files</h2>
                {fullLockGuidance()}
            </div>
        );
    }

    // Release status is released
    if (props.dataset.release_status === ("RELEASED" as ReleasedStatus)) {
        return (
            <div>
                <h2>Upload Dataset Files</h2>
                {releaseApprovedLockGuidance()}
            </div>
        );
    }

    // Release status is pending
    if (props.dataset.release_status === ("PENDING" as ReleasedStatus)) {
        return (
            <div>
                <h2>Upload Dataset Files</h2>
                {releasePendingLockGuidance()}
            </div>
        );
    }

    if (props.writeAccess) {
        return (
            <div>
                <h2>Upload Dataset Files</h2>
                {isExternal && (
                    <div style={{ marginBottom: "20px" }}>
                        <Alert variant="outlined" severity="warning">
                            <AlertTitle>Externally Reposited Data</AlertTitle>
                            This dataset has been marked as having files stored
                            externally. You may still use the provided storage
                            to host attachments or other data associated with
                            the primary dataset files.
                        </Alert>
                    </div>
                )}
                <div>
                    Your dataset was minted successfully, you can now upload the
                    dataset files. For more information about this process,
                    visit this{" "}
                    <a href={guiUploadingGuidanceLink} target="_blank">
                        link.
                    </a>{" "}
                    Start by requesting credentials using the button below.
                </div>
                <h3>Credentials</h3>
                <CredentialRequest
                    consoleURL={consoleURL}
                    creds={creds}
                    loading={datasetDetailStore.requestingAwsCreds}
                    errorMessage={datasetDetailStore.requestingAWSCredsMessage}
                    requestNewCreds={() =>
                        datasetDetailStore.generateCreds(true)
                    }
                ></CredentialRequest>
                {creds ? (
                    <React.Fragment>
                        <h3>Small and Medium Dataset</h3>

                        <Grid container justifyContent="space-between">
                            <Grid item xs={7.5}>
                                <div>
                                    If your dataset is not too large ({"<"}
                                    5GB) and you would like to use a GUI to
                                    upload your data, please follow the below
                                    steps:
                                </div>
                                <ol>
                                    <li>
                                        Open{" "}
                                        <a href={consoleURL} target="_blank">
                                            this link
                                        </a>{" "}
                                        or use the button on the right to login
                                        to the AWS system. You will be brought
                                        to your designated storage location.{" "}
                                    </li>
                                    <li>
                                        You can upload the data using the AWS
                                        console - click the orange "Upload"
                                        button, then press add files and select
                                        your dataset files.
                                    </li>
                                </ol>
                            </Grid>
                            <Grid item xs={3.5}>
                                <Stack
                                    direction="column"
                                    justifyContent="space-evenly"
                                    alignItems="stretch"
                                    style={{ height: "100%" }}
                                >
                                    <Button
                                        className={classes.guidanceButton}
                                        variant="contained"
                                        onClick={() => {
                                            window.open(consoleURL, "_blank");
                                        }}
                                    >
                                        Click to open storage location
                                    </Button>
                                    <Button
                                        className={classes.guidanceButton}
                                        variant="contained"
                                        onClick={() => {
                                            window.open(
                                                guiUploadingGuidanceLink,
                                                "_blank"
                                            );
                                        }}
                                    >
                                        Click to learn more
                                    </Button>
                                </Stack>
                            </Grid>
                        </Grid>

                        <h3>Large Dataset</h3>
                        <div>
                            If your dataset is large ({">"}5GB) or you would
                            prefer to use the AWS CLI to upload your data,
                            please follow the below steps.
                        </div>
                        <div>
                            Please note that you need to have the AWS CLI v2
                            installed to follow the below steps. For more
                            information on how to prepare your system for CLI
                            upload (and download), visit{" "}
                            <a href={cli_guidance_link} target="_blank">
                                this guide
                            </a>
                            .
                        </div>
                        <ol>
                            <li>
                                Shown below are your temporary <b>read-write</b>{" "}
                                AWS programmatic access credentials:
                                <AWSCredentialDisplay
                                    credentials={creds}
                                ></AWSCredentialDisplay>
                            </li>
                            <li>
                                Copy and paste the credentials into your AWS CLI
                                terminal environment. You can change the format
                                of the environment variable export statements
                                using the buttons above the generated
                                credentials.
                            </li>
                            <li>
                                Navigate to the system location containing the
                                dataset folder using your terminal and run the
                                aws s3 sync command. In the examples below,
                                'dataset' should be replaced with the dataset
                                folder containing the files you want to upload.
                                For example:
                                <div className={classes.code}>
                                    <CopyFloatingButton
                                        clipboardText={`aws s3 sync dataset/ ${props.dataset.s3.s3_uri}`}
                                    />
                                    aws s3 sync dataset/{" "}
                                    {props.dataset.s3.s3_uri}
                                </div>
                            </li>
                            <li>
                                You can verify your files were uploaded
                                correctly by running the following command and
                                verifying the contents are accurate:
                                <div className={classes.code}>
                                    <CopyFloatingButton
                                        clipboardText={`aws s3 ls ${props.dataset.s3.s3_uri}`}
                                    />
                                    aws s3 ls {props.dataset.s3.s3_uri}
                                </div>
                                Or by using the AWS console to preview your
                                bucket location's contents (see links in above
                                method).
                            </li>
                        </ol>
                    </React.Fragment>
                ) : null}
            </div>
        );
    }
    // not authorised!
    else {
        // This should not occur because the tab shouldn't appear
        // but it is still possible to navigate here directly
        // using the view query string
        return (
            <div>
                <h3>Unauthorised</h3>
                <p>
                    You are not authorised to write to datasets in the registry.
                    You need write access to upload dataset files. You can
                    request additional roles at the{" "}
                    <a href={LANDING_PAGE_LINK_PROFILE} target="_blank">
                        Landing Portal.
                    </a>
                </p>
            </div>
        );
    }
});

interface MetadataSummaryProps {
    dataset: ItemDataset;
    id: string;
    datasetAccess: DatasetAccess | undefined;
    locked: boolean;
}

const MetadataSummary = observer((props: MetadataSummaryProps) => {
    /**
     * Component: MetadataSummary
     * Metadata component to display a summary of the dataset metadata in
     * left hand column of the dataset detail view.
     */

    const classes = useStyles();
    const dataset = props.dataset;
    const seeUpdate = !!props.datasetAccess?.writeMetadata && !props.locked;

    const reposited =
        props.dataset.collection_format.dataset_info.access_info.reposited;

    // This is the shareable handle link
    const handleLink = "https://hdl.handle.net/" + dataset.id;

    // handleID to be copied
    const handleID = dataset.id;

    // This is the documentation for sharing datasets
    const sharingLink =
        DOCUMENTATION_BASE_URL +
        "/data-store/viewing-a-dataset.html#collaborating";

    // Try parsing times
    var d = new Date();
    // get timezone offset in ms
    const tzOffset = -d.getTimezoneOffset() * 60000;
    const createdTime = timestampToLocalTime(dataset.created_timestamp);
    const updatedTime = timestampToLocalTime(dataset.updated_timestamp);

    return (
        <div>
            <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
            >
                <h2 id="metadata-title">Metadata</h2>
                <h3>
                    Dataset Version {props.dataset.versioning_info?.version}
                </h3>
            </Stack>

            {
                // Conditionally expose the update button
                // if write privileges exist
                // Or if an error occurred during checking
                // of permissions and the user dismissed
            }
            {props.locked && shortLockGuidance}
            {seeUpdate && (
                <Button
                    variant="contained"
                    component={RouteLink}
                    to={`/update-dataset/${dataset.id}`}
                >
                    Update Metadata
                </Button>
            )}
            <h3
                style={{
                    marginBottom: 5,
                }}
            >
                Handle
            </h3>
            <Grid container>
                <Grid
                    item
                    container
                    justifyContent="center"
                    alignItems="center"
                    spacing={1}
                    marginTop={1.5}
                    marginBottom={1.5}
                    xs={12}
                >
                    <Grid>
                        <div style={{ wordWrap: "break-word" }}>
                            <a href={handleLink}>{dataset.id}</a>
                        </div>
                    </Grid>

                    <Grid
                        item
                        xs={12}
                        container
                        justifyContent="center"
                        spacing={2}
                    >
                        <Grid item>
                            <CopyButton
                                clipboardText={handleLink}
                                readyToCopyText={"Copy URL"}
                                copiedText={"URL Copied"}
                            ></CopyButton>
                        </Grid>

                        <Grid item>
                            <CopyButton
                                clipboardText={handleID}
                                readyToCopyText={"Copy ID"}
                                copiedText={"ID Copied"}
                            ></CopyButton>
                        </Grid>
                    </Grid>
                </Grid>
                <Grid xs={12}>
                    <p
                        style={{
                            marginTop: 5,
                        }}
                    >
                        You can use the handle link above to share your dataset
                        with other users. For more information about sharing
                        datasets, visit{" "}
                        <a href={sharingLink} target="_blank">
                            our documentation.
                        </a>
                    </p>
                </Grid>
            </Grid>
            {
                // We always show this now - as storage always accessible see RRAPIS-1581
            }
            <h3>Storage Location</h3>
            <div style={{ wordWrap: "break-word" }}>
                <Grid container xs={12} justifyContent="center" rowGap={2}>
                    <Grid item xs={12}>
                        <b>URI</b>: {dataset.s3.s3_uri}
                    </Grid>
                    <Grid item>
                        <CopyButton
                            clipboardText={dataset.s3.s3_uri}
                            readyToCopyText={"Click to copy S3 URI"}
                            copiedText={"URI copied"}
                        ></CopyButton>
                    </Grid>
                </Grid>
            </div>
            <h3>Record Information</h3>
            <h4>Created time</h4>
            <div>{createdTime}</div>
            <h4>Updated time</h4>
            <div>{updatedTime}</div>
        </div>
    );
});

interface MetadataSummaryWorkflowComponentProps {
    handle_id: string;
    dataset: ItemDataset;
    datasetAccess?: DatasetAccess;
    locked: boolean;
    workflowConfiguration: {
        visible: boolean;
        startingSessionId: string;
        workflowDefinition: WorkflowDefinition;
        adminMode: boolean;
        defaultExpanded: boolean;
    };
}
const MetadataSummaryWorkflowComponent = (
    props: MetadataSummaryWorkflowComponentProps
) => {
    /**
    Component: MetadataSummaryWorkflowComponent

    Combines the metadata summary component and workflow viewer (optionally displayed by default)
    
    */
    return (
        <React.Fragment>
            <MetadataSummary
                id={props.handle_id}
                dataset={props.dataset}
                datasetAccess={props.datasetAccess}
                locked={props.locked}
            ></MetadataSummary>
            {props.workflowConfiguration.visible && (
                <WorkflowViewComponent
                    startingSessionId={
                        props.workflowConfiguration.startingSessionId
                    }
                    workflowDefinition={
                        props.workflowConfiguration.workflowDefinition
                    }
                    defaultExpanded={
                        props.workflowConfiguration.defaultExpanded
                    }
                    adminMode={props.workflowConfiguration.adminMode}
                />
            )}
        </React.Fragment>
    );
};

interface ApprovalsComponentProps {
    dataset: ItemDataset;
}

const ApprovalsComponent = (props: ApprovalsComponentProps) => {
    /**
    * Component: DatasetDetailsComponent

    * This component renders the Details tab content
    */

    return props.dataset ? (
        <div style={{ width: "inherit" }}>
            <h2>Approvals</h2>
            <ApprovalsTabView dataset={props.dataset} />
        </div>
    ) : (
        <Grid>
            <CircularProgress />
        </Grid>
    );
};

interface UpdateMetadataParams {
    id: string;
}

interface DatasetDetailProps {}

const DatasetDetail = observer((props: DatasetDetailProps) => {
    const classes = useStyles();
    const { id: handle_id } = useParams<UpdateMetadataParams>();

    // Use auth
    const readCheck = useAccessCheck({
        componentName: "entity-registry",
        desiredAccessLevel: "READ",
    });
    const writeCheck = useAccessCheck({
        componentName: "entity-registry",
        desiredAccessLevel: "WRITE",
    });

    const breadcrumbLinks = [
        {
            link: "/",
            label: "Home",
        },
        {
            link: "/datasets",
            label: "Datasets",
        },
        {
            link: `/dataset/${handle_id}`,
            label: `${handle_id}`,
        },
    ];

    // Header content which includes breadcrumbs and link to view in registry
    const registryLink = REGISTRY_LINK + `/item/${handle_id}`;

    // check if a view is present - use overview as default
    const defaultView = "overview";
    // valid actions upload, download, overview
    const { value: rawDesiredView, setValue: setDesiredView } =
        useQueryStringVariable({
            queryStringKey: "view",
            defaultValue: defaultView,
            readOnly: false,
        });

    // Take away possibly undefined
    const desiredView = rawDesiredView ?? defaultView;

    const [datasetAccess, setDatasetAccess] = useState<
        DatasetAccess | undefined
    >(undefined);

    // Keycloak
    const { keycloak } = useKeycloak();

    // These are derived from the dataset access object, see authHelpers
    // deriveDatasetAccess function
    const reposited =
        datasetDetailStore.datasetDetail?.collection_format.dataset_info
            .access_info.reposited ?? false;

    // We always show this as long as access sufficient now - as storage always accessible see RRAPIS-1581

    // prev
    //const seeDownload = !!datasetAccess?.readData && reposited;
    //const seeUpload = !!datasetAccess?.writeData && reposited;

    const seeDownload = !!datasetAccess?.readData;
    const seeUpload = !!datasetAccess?.writeData;
    const seeExternalAccess =
        readCheck.fallbackGranted &&
        datasetAccess?.readData &&
        datasetDetailStore.datasetDetail &&
        !reposited;
    const seeSettingsAdminRequiredContent = !!datasetAccess?.admin;
    const seeCloneButton =
        // Must have metadata write
        writeCheck.fallbackGranted &&
        // Must have entity loaded
        datasetDetailStore.datasetDetail;
    const seeApprovals = !!datasetAccess?.admin;

    // Ready to download?
    const readyToFetch = readCheck.fallbackGranted;

    // This useQuery manages downloading the dataset and updating some store
    // components upon successful download
    const {
        isFetching: datasetLoading,
        isError,
        error,
        refetch: refetchDataset,
    } = useQuery({
        queryKey: [handle_id],
        queryFn: () => {
            return fetchDataset(handle_id);
        },
        onSuccess(data) {
            // Trigger other loads and updates to state

            // Store the item and roles from fetch response
            datasetDetailStore.datasetDetail = data.item;
            datasetDetailStore.roles = data.roles;
            datasetDetailStore.locked = data.locked;

            // Derive fine grained access information from the roles
            setDatasetAccess(deriveDatasetAccess(data.roles));
        },
        enabled: readyToFetch,
    });

    const handleTabChange = (newTab: any) => {
        setDesiredView!(newTab || desiredView);
    };
    const initialDataset = datasetDetailStore.datasetDetail;
    const locked = datasetDetailStore.locked ?? false;

    // Manage the versioning state and revert workflow

    // We need to track the desired version which defaults to undefined (latest)
    // We can then use the driven historical item to manage this

    // use version selector to manage state and controls over version
    const versionControls = useMetadataHistorySelector({
        item: initialDataset as unknown as ItemBase,
    });

    // Manage with hook
    const {
        currentItem: baseDataset,
        isLatest,
        latestId,
        error: historyError,
        errorMessage: historyErrorMessage,
    } = useHistoricalDrivenItem<ItemBase>({
        item: initialDataset as unknown as ItemBase,
        historicalId: versionControls.state?.historyId,
    });
    const dataset = baseDataset as ItemDataset;

    // use revert item hook and dialog to manage revert ops if any
    const onRevertFinished = (res: ItemRevertResponse) => {
        // Reset the state to reload the item and reset version to undefined (i.e. latest)
        versionControls.controls?.manuallySetId(undefined);
        // Force a reload of typed item contents
        refetchDataset();
    };
    const revertControls = useRevertDialog({
        id: initialDataset?.id,
        historyId: versionControls.state?.historyId,
        onSuccess: onRevertFinished,
        subtype: "DATASET",
        context: "data-store",
    });

    // Workflow
    // --------

    // Manage parsing and determining access for workflow visualiser
    const workflowConfiguration = useWorkflowHelper({
        // Error in pydantic2ts which makes category optional - this is fine
        item: dataset as ItemBase,
    });

    // Define the error dialog fragment in case something goes wrong with the
    // access check process
    const accessState = combineLoadStates([readCheck, writeCheck]);
    const dialogFragments = (
        <React.Fragment>
            {
                //Error dialogue based on store state
            }
            <Dialog open={accessState.error}>
                <DialogTitle> Access check error! </DialogTitle>
                <DialogContent>
                    <DialogContent>
                        <p>
                            The system experienced an issue while trying to
                            check your system access. <br />
                            Error message:{" "}
                            {accessState.errorMessage ??
                                "No error message provided."}
                            <br />
                            Try refreshing. If you are definitely authorised and
                            still see this error, please use the{" "}
                            <i>Contact Us</i> link to report an issue.
                        </p>
                    </DialogContent>
                </DialogContent>
            </Dialog>
        </React.Fragment>
    );

    // body content depends on state
    var bodyContent: JSX.Element = <></>;

    const loadingBodyContent = (
        <Backdrop open={true}>
            <CircularProgress />
        </Backdrop>
    );

    const errorBodyContent = (
        <Grid container>
            <Grid xs={12}>
                <h3>An error occurred</h3>
                <p>
                    Something went wrong when loading the dataset. <br></br>
                    Error message: {error ?? "Unknown"}
                    <br></br>
                    Try refreshing the page and ensure you have read
                    permissions. If this error persists please contact us using
                    the <i>Contact Us</i> link.
                </p>
            </Grid>
        </Grid>
    );

    const invalidObjectBodyContent = (
        <Grid container>
            <Grid xs={12}>
                <h3>An error occurred</h3>
                <p>
                    It appears that the registry returned an invalid object.
                    Please try refreshing and check your access permissions. If
                    this error persists please contact us using the{" "}
                    <i>Contact Us</i> link.
                </p>
            </Grid>
        </Grid>
    );

    const headerContent = (
        <Stack direction="row" justifyContent={"space-between"}>
            <BreadcrumbLinks links={breadcrumbLinks} />
            {
                //RH button and versioning group
            }
            <div>
                <Stack
                    direction="row"
                    spacing={2}
                    justifyContent="flex-end"
                    alignItems="center"
                    divider={<Divider flexItem orientation="vertical" />}
                >
                    <Stack direction="row" spacing={1}>
                        {
                            // Clone button (sometimes)
                        }
                        {seeCloneButton && (
                            <Button
                                variant="outlined"
                                href={`/clone-dataset/${handle_id}`}
                            >
                                Clone Dataset
                            </Button>
                        )}
                        {
                            // View in reg button
                        }
                        <Button
                            variant="outlined"
                            onClick={() => {
                                window.open(
                                    registryLink,
                                    "_blank",
                                    "noopener,noreferrer"
                                );
                            }}
                        >
                            View in registry{" "}
                            <LaunchIcon style={{ marginLeft: "10px" }} />
                        </Button>
                    </Stack>
                </Stack>
            </div>
        </Stack>
    );

    const getCustomisedMetadataSummary = (showWorkflowDefault: boolean) => {
        return (
            <MetadataSummaryWorkflowComponent
                handle_id={handle_id}
                dataset={dataset!}
                datasetAccess={datasetAccess}
                locked={locked}
                workflowConfiguration={{
                    visible: workflowConfiguration.visible,
                    startingSessionId: workflowConfiguration.startingSessionId!,
                    workflowDefinition:
                        workflowConfiguration.workflowDefinition!,
                    defaultExpanded: showWorkflowDefault,
                    adminMode: workflowConfiguration.adminMode,
                }}
            />
        );
    };

    // Ensure that dataset is not undefined before trying to render this segment!
    const mainBodyContent = (
        <Grid container className={classes.dataset}>
            <Grid xs={12} className={classes.panelContext}>
                <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                    <Tabs
                        value={desiredView}
                        onChange={(e, value) => handleTabChange(value)}
                        variant="scrollable"
                        scrollButtons="auto"
                    >
                        <Tab
                            label={"Overview"}
                            value={"overview"}
                            component={RouteLink}
                            to={`/dataset/${handle_id}?view=overview`}
                        ></Tab>
                        <Tab
                            label={"Details"}
                            value={"details"}
                            component={RouteLink}
                            to={`/dataset/${handle_id}?view=details`}
                        ></Tab>
                        <Tab
                            label={"Lineage Graph"}
                            value={"lineage"}
                            component={RouteLink}
                            to={`/dataset/${handle_id}?view=lineage`}
                        ></Tab>
                        <Tab
                            label={"Versioning"}
                            value={"versioning"}
                            component={RouteLink}
                            to={`/dataset/${handle_id}?view=versioning`}
                        ></Tab>
                        {
                            // conditionally show tabs based on dataset and
                            // general access permission
                        }
                        {seeDownload && (
                            <Tab
                                label={"Download Data"}
                                value={"download"}
                                component={RouteLink}
                                to={`/dataset/${handle_id}?view=download`}
                            ></Tab>
                        )}
                        {seeUpload && (
                            <Tab
                                label={"Upload Data"}
                                value={"upload"}
                                component={RouteLink}
                                to={`/dataset/${handle_id}?view=upload`}
                            ></Tab>
                        )}
                        {seeExternalAccess && (
                            <Tab
                                label={"External Access"}
                                value={"external"}
                                component={RouteLink}
                                to={`/dataset/${handle_id}?view=external`}
                            ></Tab>
                        )}
                        {seeApprovals && (
                            <Tab
                                label={"Approvals"}
                                value={"approvals"}
                                component={RouteLink}
                                to={`/dataset/${handle_id}?view=approvals`}
                            ></Tab>
                        )}
                        <Tab
                            label={"Settings"}
                            value={"settings"}
                            component={RouteLink}
                            to={`/dataset/${handle_id}?view=settings`}
                        ></Tab>
                    </Tabs>
                </Box>
                <TabPanel index={"overview"} currentIndex={desiredView}>
                    <Grid container className={classes.tabs}>
                        <Grid xs={4} className={classes.metadataOverview}>
                            {getCustomisedMetadataSummary(true)}
                        </Grid>
                        <Grid xs={8} className={classes.tabsRHContent}>
                            <PreviewDataset dataset={dataset!} />
                        </Grid>
                    </Grid>
                </TabPanel>
                <TabPanel index={"details"} currentIndex={desiredView}>
                    <Grid container className={classes.tabs}>
                        <DatasetDetailsComponent
                            dataset={dataset! as unknown as ItemBase}
                        />
                    </Grid>
                </TabPanel>
                <TabPanel index={"lineage"} currentIndex={desiredView}>
                    <Grid container className={classes.tabs}>
                        <LineageGraphComponent rootID={handle_id} />
                    </Grid>
                </TabPanel>
                <TabPanel index={"versioning"} currentIndex={desiredView}>
                    <Grid container className={classes.tabs}>
                        <VersioningViewComponent
                            item={dataset as ItemBase}
                            isAdmin={!!datasetAccess?.admin}
                        />
                    </Grid>
                </TabPanel>
                {
                    // conditionally show tabs based on dataset and
                    // general access permission
                }
                {seeDownload && (
                    <TabPanel index={"download"} currentIndex={desiredView}>
                        <Grid container className={classes.tabs}>
                            <Grid xs={4} className={classes.metadataOverview}>
                                {getCustomisedMetadataSummary(false)}
                            </Grid>
                            <Grid xs={8} className={classes.tabsRHContent}>
                                <DownloadGuidance dataset={dataset!} />
                            </Grid>
                        </Grid>
                    </TabPanel>
                )}
                {seeUpload && (
                    <TabPanel index={"upload"} currentIndex={desiredView}>
                        <Grid container className={classes.tabs}>
                            <Grid xs={4} className={classes.metadataOverview}>
                                {getCustomisedMetadataSummary(false)}
                            </Grid>
                            <Grid xs={8} className={classes.tabsRHContent}>
                                <UploadGuidance
                                    locked={locked}
                                    dataset={dataset!}
                                    writeAccess={datasetAccess?.writeData}
                                />
                            </Grid>
                        </Grid>
                    </TabPanel>
                )}
                {seeExternalAccess && (
                    <TabPanel index={"external"} currentIndex={desiredView}>
                        <Grid container className={classes.tabs}>
                            <ExternalAccess dataset={dataset!} />
                        </Grid>
                    </TabPanel>
                )}
                {seeApprovals && (
                    <TabPanel index={"approvals"} currentIndex={desiredView}>
                        <Grid container className={classes.tabs}>
                            <ApprovalsComponent dataset={dataset!} />
                        </Grid>
                    </TabPanel>
                )}
                <TabPanel index={"settings"} currentIndex={desiredView}>
                    <Grid container className={classes.tabs}>
                        {/* Metadata history */}
                        <Stack
                            direction="column"
                            spacing={2}
                            className={classes.fullWidth}
                        >
                            <MetadataHistory
                                hide={historyError}
                                locked={locked}
                                writeAccessGranted={
                                    writeCheck.fallbackGranted &&
                                    !!datasetAccess?.writeMetadata
                                }
                                isLatest={isLatest ?? true}
                                latestId={latestId}
                                versionControls={versionControls}
                                revertControls={revertControls}
                            />
                            <Divider />
                            <Grid item xs={12}>
                                <h2>Settings</h2>
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body1">
                                    View this item in the{" "}
                                    <a
                                        href={registryLink + "?view=settings"}
                                        target="_blank"
                                        referrerPolicy={"no-referrer"}
                                    >
                                        registry
                                    </a>{" "}
                                    to manage it's settings.
                                </Typography>
                            </Grid>
                        </Stack>
                    </Grid>
                </TabPanel>
            </Grid>
        </Grid>
    );

    const unauthorisedBodyContent = (
        <Grid container>
            <Grid xs={12}>
                <h3>Unauthorised</h3>
                <p>
                    You have insufficient permissions to view{" "}
                    {readCheck.fallbackGranted ? "this item" : "data"} in the
                    data store registry.{" "}
                    {!readCheck.fallbackGranted && (
                        <p>
                            You can manage your roles at the{" "}
                            <a href={LANDING_PAGE_LINK_PROFILE}>
                                Landing Portal.
                            </a>
                        </p>
                    )}
                </p>
            </Grid>
        </Grid>
    );

    // Is it still loading?
    if (
        datasetLoading ||
        (!readCheck.fallbackGranted && readCheck.loading) ||
        (!readCheck.fallbackGranted && writeCheck.loading)
    ) {
        bodyContent = loadingBodyContent;
    } else if (isError) {
        // Finished loading but there was an error
        // or finished loading there was no error but
        // dataset is not defined!
        bodyContent = errorBodyContent;
    } else if (readCheck.fallbackGranted && datasetAccess?.readMetadata) {
        // If authorised or bypassing
        // Should have dataset by now!
        if (!dataset) {
            bodyContent = invalidObjectBodyContent;
        } else {
            // primary case
            bodyContent = mainBodyContent;
        }
    } else {
        // Unauthorised!
        bodyContent = unauthorisedBodyContent;
    }

    // Always return this structure
    return (
        <div className={classes.root}>
            {versionControls.render()}
            {revertControls.render()}
            {dialogFragments}
            <Stack>
                {headerContent}
                {bodyContent}
            </Stack>
        </div>
    );
});

export default DatasetDetail;
