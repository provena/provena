import {
    Alert,
    Button,
    CircularProgress,
    Divider,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import {
    DOCUMENTATION_BASE_URL,
    Swatches,
    keycloak,
    useCombinedLoadedItem,
    useQueryStringVariable,
} from "react-libs";
import { ItemDisplayWithStatusComponent } from "../components/ItemDisplayWithStatus";
import ProvGraph from "../components/ProvGraph";
import accessStore from "../stores/accessStore";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        topPanelContainer: {
            marginBottom: theme.spacing(2),
        },
        topPanel: {
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(3),
            borderRadius: 5,
        },
        bodyPanelContainer: {
            margin: theme.spacing(0),
        },
        bodyProgressContainer: {
            display: "flex",
            alignItems: "center",
            margin: theme.spacing(0),
        },
        recordInfoContainer: {},
        recordInfoPanel: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "start",
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(4),
            borderRadius: 5,
        },
        metadataPanel: {
            paddingTop: theme.spacing(2),
        },
        accessInteractionContainer: {
            display: "flex",
            flexDirection: "column",
        },
        accessAPIContainer: {
            paddingBottom: theme.spacing(1),
        },
        accessAPIPanel: {
            display: "flex",
            flexDirection: "column",
            justifyContent: "start",
            alignItems: "left",
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(4),
            borderRadius: 5,
        },
        interactionContainer: {
            paddingTop: theme.spacing(1),
        },
        interactionPanel: {
            display: "flex",
            justifyContent: "space-around",
            alignItems: "center",
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(2),
            borderRadius: 5,
        },
        ioContainer: {
            display: "flex",
            justifyContent: "space-around",
            alignItems: "center",
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(2),
            borderRadius: 5,
        },
        ioPanel: {
            marginTop: theme.spacing(2),
        },
        itemInformationPanel: {},
        actionButton: {
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(3),
        },
        itemPropertyContainer: {
            marginBottom: theme.spacing(1),
        },
        itemPropertyName: {
            fontWeight: theme.typography.fontWeightBold,
        },
        lineDivider: {
            height: "1px",
            backgroundColor: theme.palette.divider,
            marginBottom: theme.spacing(3),
        },
        detailsContainer: {
            paddingLeft: theme.spacing(2),
            paddingRight: theme.spacing(2),
        },
        rootRecordDetailsContainer: {
            maxHeight: "400px",
            overflowY: "scroll",
        },
        hidden: {
            display: "none",
        },
        alert: {
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            paddingBottom: theme.spacing(1),
            paddingTop: theme.spacing(1),
            width: "100%",
        },
    })
);

export const rootIdQueryStringKey = "rootId";

const safeConvertToLocaleDate = (timestamp?: number | undefined) => {
    if (!timestamp) return undefined;
    let date = new Date(timestamp * 1000);
    return `${date.toLocaleDateString("en-AU")} ${date.getHours()}:${
        date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes()
    } ${date.getHours() < 12 ? "AM" : "PM"}`;
};

interface LegendProps {
    colour: string;
    acronym: string;
    name: object;
}
const LegendItem = (props: LegendProps) => {
    return (
        <Grid
            container
            item
            xs={12}
            sx={{
                textAlign: "end",
                justifyContent: "space-around",
                flexDirection: "row",
                marginBottom: "12px",
            }}
        >
            <Grid container item xs={2} sx={{ justifyContent: "end" }}>
                <Grid
                    item
                    sx={{
                        backgroundColor: props.colour,
                        width: "25px",
                        height: "25px",
                        borderRadius: "13px",
                    }}
                ></Grid>
            </Grid>
            <Grid
                container
                item
                xs={2}
                sx={{ justifyContent: "center", paddingTop: "4px" }}
            >
                <Typography variant="caption">{props.acronym}</Typography>
            </Grid>
            <Grid
                container
                item
                xs={8}
                sx={{ justifyContent: "start", paddingTop: "4px" }}
            >
                <Typography variant="caption">&nbsp;{props.name}</Typography>
            </Grid>
        </Grid>
    );
};

const View = observer(() => {
    const classes = useStyles();

    // Trigger access store check on keycloak auth update
    useEffect(() => {
        accessStore.checkAccess();
    }, [keycloak.authenticated]);

    // Manage root node Id with query string controlled stateful variable
    const { value: rootId, setValue: setRootId } = useQueryStringVariable({
        queryStringKey: rootIdQueryStringKey,
    });

    // Is there a selected rootId?
    const rootIdSelected = rootId !== "";

    // Graph state
    const [graphExpanded, setGraphExpanded] = useState<boolean>(false);

    // Removed : if entity ID changes => reset focussed entity

    // Does the access store imply that we are ready to query for the item?
    const readyToQuery =
        // Ensure handle is defined
        rootIdSelected &&
        // And either error bypassed or the access store provides read access
        (accessStore.forceErrorBypass ||
            ((accessStore.registryReadAccess ?? false) && !accessStore.error));

    // Load the item
    const loadedItem = useCombinedLoadedItem({
        id: rootId,
        disabled: !readyToQuery,
    });

    // States
    const loadingItem = loadedItem.loading || accessStore.loading;
    const fetchErrorOccurred = loadedItem.error;
    const accessErrorOccurred = accessStore.error;
    const readAccessDeniedGlobal =
        accessStore.registryReadAccess !== undefined &&
        !accessStore.registryReadAccess;
    const errorMessage = loadedItem.errorMessage || accessStore.errorMessage;

    return (
        <Grid container>
            <Grid container item className={classes.topPanelContainer}>
                <Grid
                    id="title-text"
                    container
                    item
                    className={classes.topPanel}
                >
                    <Typography variant="h5">
                        {graphExpanded === false
                            ? "Viewing Entity Record"
                            : "Expanded Graph View"}
                    </Typography>
                </Grid>
            </Grid>
            <Grid
                id="rootEntityPanel"
                container
                item
                xs={12}
                className={graphExpanded === false ? "" : classes.hidden}
            >
                <Grid
                    container
                    item
                    xs={12}
                    className={classes.recordInfoPanel}
                >
                    <Grid
                        container
                        item
                        xs={12}
                        className={classes.bodyPanelContainer}
                    >
                        {readAccessDeniedGlobal && (
                            <Alert
                                className={classes.alert}
                                severity="error"
                                action={
                                    <Button variant="outlined" href="/profile">
                                        Request Access
                                    </Button>
                                }
                            >
                                You do not have sufficient registry store
                                permissions to view entity record details.
                            </Alert>
                        )}
                        {accessErrorOccurred && (
                            <Alert className={classes.alert} severity="error">
                                An error occurred while determining access
                                error:{" "}
                                {errorMessage ??
                                    "Unknown - check console and contact us for help."}
                            </Alert>
                        )}
                        {fetchErrorOccurred && (
                            <>
                                <Alert
                                    className={classes.alert}
                                    severity="error"
                                >
                                    An error occurred while fetching the root
                                    entity, error:{" "}
                                    {errorMessage ??
                                        "Unknown - check console and contact us for help."}
                                </Alert>
                            </>
                        )}
                        <Grid
                            container
                            item
                            md={6}
                            lg={8}
                            sx={{ paddingTop: "5px", paddingBottom: "8px" }}
                        >
                            <Stack
                                divider={<Divider flexItem />}
                                spacing={1.5}
                                style={{ width: "100%" }}
                            >
                                <Typography variant="h6">
                                    Root Record Details
                                </Typography>
                                <div
                                    className={
                                        classes.rootRecordDetailsContainer
                                    }
                                    style={{ height: "100%" }}
                                >
                                    <ItemDisplayWithStatusComponent
                                        id={rootId ?? "NA"}
                                        disabled={!readyToQuery}
                                        status={loadedItem}
                                        layout="column"
                                        columnLayout={{
                                            columnSpace: 0.5,
                                            propertyNameBase: 4,
                                            propertyValueBase: 8,
                                        }}
                                    />
                                </div>
                            </Stack>
                        </Grid>
                        <Grid container item md={6} lg={4}>
                            <Grid
                                container
                                item
                                xs={12}
                                sx={{
                                    justifyContent: "end",
                                    marginLeft: "12px",
                                }}
                            >
                                <Grid
                                    item
                                    xs={12}
                                    sx={{
                                        flexDirection: "column",
                                        padding: "12px",
                                        border: "1px dotted black",
                                        borderRadius: "5px",
                                    }}
                                >
                                    <Typography variant="h6">Legend</Typography>
                                    <Divider
                                        sx={{
                                            width: "100%",
                                            marginBottom: "12px",
                                        }}
                                    />
                                    <LegendItem
                                        colour={Swatches.personSwatch.colour}
                                        acronym="P"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/establishing-required-entities#person"}
                                                    target="_blank"
                                                >
                                                    Person
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={
                                            Swatches.organisationSwatch.colour
                                        }
                                        acronym="O"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/establishing-required-entities#organisation"}
                                                    target="_blank"
                                                >
                                                    Organisation
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={Swatches.datasetSwatch.colour}
                                        acronym="D"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/data-store/overview#data-store-overview"}
                                                    target="_blank"
                                                >
                                                    Dataset
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={
                                            Swatches.datasetTemplateSwatch
                                                .colour
                                        }
                                        acronym="DT"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/model-workflow-configuration.html#dataset-template"}
                                                    target="_blank"
                                                >
                                                    Dataset Template
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={Swatches.modelSwatch.colour}
                                        acronym="M"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/establishing-required-entities#model"}
                                                    target="_blank"
                                                >
                                                    Model
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={Swatches.modelRunSwatch.colour}
                                        acronym="MR"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/registration-process/overview.html#model-run-overview"}
                                                    target="_blank"
                                                >
                                                    Model Run
                                                </a>
                                            </span>
                                        }
                                    />
                                    <LegendItem
                                        colour={
                                            Swatches
                                                .modelRunWorkflowDefinitionSwatch
                                                .colour
                                        }
                                        acronym="MRWT"
                                        name={
                                            <span>
                                                <a
                                                    href={DOCUMENTATION_BASE_URL + "/information-system/provenance/registering-model-runs/model-workflow-configuration#model-run-workflow-template"}
                                                    target="_blank"
                                                >
                                                    Model Run Workflow Template
                                                </a>
                                            </span>
                                        }
                                    />
                                </Grid>
                            </Grid>
                        </Grid>

                        {loadingItem && (
                            <Grid container item xs={12}>
                                <Grid
                                    container
                                    item
                                    xs={12}
                                    direction="column"
                                    justifyContent={"center"}
                                    alignContent="center"
                                >
                                    <CircularProgress />
                                </Grid>
                                <Grid
                                    container
                                    item
                                    xs={12}
                                    direction="column"
                                    justifyContent={"center"}
                                    alignContent="center"
                                >
                                    <Typography variant="body1">
                                        Loading entity details and determining
                                        access...
                                    </Typography>
                                </Grid>
                            </Grid>
                        )}
                    </Grid>
                </Grid>
            </Grid>

            <Grid
                id="graphPanel"
                container
                item
                xs={12}
                className={classes.metadataPanel}
            >
                <Grid
                    container
                    item
                    xs={12}
                    className={classes.accessAPIContainer}
                >
                    <Grid
                        container
                        item
                        xs={12}
                        className={classes.accessAPIPanel}
                    >
                        {
                            // Show the prov graph as long as read access is available -
                            //even if there is an error loading the root node we may still explore e.g. 401 error
                        }
                        {!readAccessDeniedGlobal && (
                            <ProvGraph
                                rootId={rootId!}
                                setRootId={setRootId!}
                                toggleExpanded={() => {
                                    setGraphExpanded((old) => !old);
                                }}
                                expanded={graphExpanded}
                            />
                        )}
                    </Grid>
                </Grid>
            </Grid>
        </Grid>
    );
});

export default View;
