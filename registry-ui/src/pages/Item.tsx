import KeyboardArrowLeft from "@mui/icons-material/KeyboardArrowLeft";
import KeyboardArrowRight from "@mui/icons-material/KeyboardArrowRight";
import LaunchIcon from "@mui/icons-material/Launch";
import LockIcon from "@mui/icons-material/Lock";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Icon,
  IconButton,
  Stack,
  Tab,
  Tabs,
  Tooltip,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import ItemView from "components/ItemView";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import {
  DATA_STORE_LINK,
  DOCUMENTATION_BASE_URL,
  LANDING_PAGE_LINK_PROFILE,
  PROV_STORE_LINK,
  ResourceAccess,
  TabPanel,
  VersioningView,
  WorkflowVisualiserComponent,
  combineLoadStates,
  deriveResourceAccess,
  mapSubTypeToPrettyName,
  subtypeHasVersioning,
  useAccessCheck,
  useHistoricalDrivenItem,
  useMetadataHistorySelector,
  useQueryStringVariable,
  useRevertDialog,
  useTypedLoadedItem,
  useUntypedLoadedItem,
  useUserLinkServiceLookup,
  MetadataHistory,
  useWorkflowHelper,
} from "react-libs";
import { Link as RouteLink, useParams } from "react-router-dom";
import { registryVersionIdLinkResolver } from "util/helper";
import { nonEditEntityTypes } from "../entityLists";
import { ItemRevertResponse } from "../provena-interfaces/RegistryAPI";
import {
  ItemBase,
  ItemSubType,
  ItemModelRun,
} from "../provena-interfaces/RegistryModels";

import { AccessControl } from "../subpages/settings-panel/AccessSettings";
import { LockSettings } from "../subpages/settings-panel/LockSettings";
import { GenericFetchResponse } from "react-libs/provena-interfaces/RegistryAPI";
import { useAddStudyLinkDialog } from "hooks/useAddStudyLinkDialog";
import { useGenerateReportDialog } from "react-libs/hooks/useGenerateReportDialog";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    topPanelContainer: {
      marginBottom: theme.spacing(2),
    },
    topPanel: {
      backgroundColor: theme.palette.common.white,
      paddingTop: theme.spacing(1),
      paddingBottom: theme.spacing(1),
      paddingLeft: theme.spacing(3),
      paddingRight: theme.spacing(3),
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
    recordInfoContainer: {
      paddingRight: theme.spacing(1),
    },
    recordInfoPanel: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      alignItems: "stretch",
      width: "100%",
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(4),
      borderRadius: 5,
    },
    metadataPanel: {
      paddingLeft: theme.spacing(1),
      maxHeight: "400px",
    },
    accessInteractionContainer: {
      display: "flex",
      flexDirection: "column",
    },
    accessAPIContainer: {
      paddingBottom: theme.spacing(1),
      maxHeight: "200px",
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
      maxHeight: "200px",
    },
    interactionPanel: {
      display: "flex",
      justifyContent: "space-around",
      alignItems: "center",
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(2),
      borderRadius: 5,
    },
    itemInformationPanel: {
      marginTop: theme.spacing(2),
    },
    actionButton: {},
    workflowView: {
      width: "100%",
      boxShadow: "0 0 2px 0 rgba( 31, 38, 135, 0.37 )",
      marginLeft: theme.spacing(2),
      paddingTop: theme.spacing(0),
      paddingRight: theme.spacing(2),
    },
    itemView: {
      flex: 1,
      paddingTop: theme.spacing(0),
    },
  })
);

type ItemParams = {
  idPrefix: string;
  idSuffix: string;
};

const resourceLockLink =
  DOCUMENTATION_BASE_URL + "/registry/resource_lock.html";

export const lockedResourceContent = (
  // HTML example is from MUI documentation
  <Tooltip
    title={
      <React.Fragment>
        <Typography color="inherit">This resource is locked.</Typography>
        This resource is locked and cannot be modified. To learn more about
        resource locks, see{" "}
        <a href={resourceLockLink} target="_blank" rel="noreferrer">
          our documentation
        </a>
        .
      </React.Fragment>
    }
  >
    <LockIcon fontSize="large" />
  </Tooltip>
);

type Views = "overview" | "settings" | "versioning";
const overviewView = "overview" as Views;
const settingsView = "settings" as Views;
const versioningView = "versioning" as Views;

const RecordView = observer((props: {}) => {
  // Use auth
  const readCheck = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "READ",
  });
  const writeCheck = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });
  const userLink = useUserLinkServiceLookup({});
  const userPersonId: string | undefined = userLink.data;

  // Get classes
  const classes = useStyles();

  // links
  const requestingAccessLink =
    DOCUMENTATION_BASE_URL + "/getting-started-is/requesting-access-is.html";
  const registryAccessLink =
    DOCUMENTATION_BASE_URL + "/registry/access-control.html";
  // Pull out the ID component of path (post /item)
  const params = useParams<ItemParams>();

  // Construct a handle ID from the params if present
  var handleId: string | undefined = undefined;

  if (params && params.idPrefix && params.idSuffix) {
    handleId = `${params.idPrefix}/${params.idSuffix}`;
  }

  // check if a view query string is present
  const defaultView: Views = overviewView;

  // Manage the current view
  const { value: desiredView, setValue: setDesiredView } =
    useQueryStringVariable({
      queryStringKey: "view",
      // Use default view if none provided
      defaultValue: defaultView,
    });

  // Keep state for this and default to overview
  const handleTabChange = (newTab: any) => {
    setDesiredView!(newTab || desiredView);
  };

  // Copy state
  const [handleCopied, setHandleCopied] = useState<boolean>(false);

  // Does the access store imply that we are ready to query for the item?
  const readyToQueryUntyped =
    // Ensure handle is defined
    handleId !== undefined &&
    // And either error bypassed or the access store provides read access
    readCheck.granted;

  // Hook to load untyped item
  const {
    data: untypedItem,
    loading: untypedLoading,
    error: untypedIsError,
    errorMessage: untypedErrorMessage,
  } = useUntypedLoadedItem({ id: handleId, enabled: readyToQueryUntyped });

  // Decode the item subtype if loaded and successful
  const subtype: ItemSubType | undefined = untypedItem?.item_subtype;

  // Hook to load typed item
  const readyToQueryTyped =
    // Ensure untyped item and item subtype are decoded
    untypedItem !== undefined && subtype !== undefined;

  // Hook to load typed item
  const {
    item: typedItem,
    data: typedPayload,
    loading: typedLoading,
    error: typedIsError,
    errorMessage: typedErrorMessage,
    refetch: refetchLoadedItem,
  } = useTypedLoadedItem({
    id: handleId,
    subtype: subtype,
    enabled: readyToQueryTyped,
  });

  // Need to derive this access when the item is fetched
  const [resourceAccess, setResourceAccess] = useState<
    ResourceAccess | undefined
  >(undefined);

  useEffect(() => {
    if (typedPayload !== undefined) {
      setResourceAccess(deriveResourceAccess(typedPayload.roles ?? []));
    }
  }, [typedPayload]);

  // Are we locked?
  const [locked, setLocked] = useState<boolean>(false);

  // Track this as state so we can hotswap it
  useEffect(() => {
    setLocked(typedPayload?.locked ?? false);
  }, [typedPayload?.locked]);

  // Version state

  // We need to track the desired version which defaults to undefined (latest)
  // We can then use the driven historical item to manage this

  // use version selector to manage state and controls over version
  const versionControls = useMetadataHistorySelector({
    item: typedItem,
  });

  // Manage with hook
  const {
    currentItem: item,
    isLatest,
    latestId,
    error: historyError,
    errorMessage: historyErrorMessage,
  } = useHistoricalDrivenItem<ItemBase>({
    item: typedItem,
    historicalId: versionControls.state?.historyId,
  });

  // use revert item hook and dialog to manage revert ops if any
  const onRevertFinished = (res: ItemRevertResponse) => {
    // Reset the state to reload the item and reset version to undefined (i.e. latest)
    versionControls.controls?.manuallySetId(undefined);
    // Force a reload of typed item contents
    refetchLoadedItem();
  };
  const revertControls = useRevertDialog({
    id: typedItem?.id,
    historyId: versionControls.state?.historyId,
    subtype,
    onSuccess: onRevertFinished,
  });

  // Workflow
  // --------

  // Handle expand and collapse for workflow visualiser, default to show
  const [workflowViewExpanded, setWorkflowViewExpanded] =
    useState<boolean>(true);

  // Manage parsing and determining access for workflow visualiser
  const workflowConfiguration = useWorkflowHelper({ item: item });

  // Derive write access statea
  const writeAccessGranted = !!resourceAccess?.writeMetadata;

  const seeMetadataUpdate =
    // Must not be locked
    !locked &&
    // Must have metadata write
    writeAccessGranted &&
    // Must have entity loaded and subtype parsed
    item !== undefined &&
    subtype !== undefined &&
    // Must be editable type
    nonEditEntityTypes.indexOf(subtype) === -1;

  const seeCloneButton =
    // Must have metadata write
    writeCheck.fallbackGranted &&
    // Must have entity loaded and subtype parsed
    item !== undefined &&
    subtype !== undefined &&
    // Must be editable type
    nonEditEntityTypes.indexOf(subtype) === -1;

  const seeVersioning = !!subtype && subtypeHasVersioning(subtype);

  const seeSettingsAdminRequiredContent = !!resourceAccess?.admin;
  const headerName = subtype ? mapSubTypeToPrettyName(subtype) : "Entity";

  const isDataset = subtype === "DATASET";
  const isModelRun = subtype === "MODEL_RUN";
  const isLinkedToStudy =
    isModelRun &&
    typedPayload &&
    !!(typedPayload.item as ItemModelRun).record.study_id;

  // Checking whether we should render the "Generate Report Button"
  const isStudy = subtype === "STUDY"
  const isModelRunOrStudy =
    isStudy || isModelRun &&
    typedPayload

  const datastoreLink = isDataset
    ? `${DATA_STORE_LINK}/dataset/${params.idPrefix}/${params.idSuffix}`
    : undefined;

  // States
  const isUser =
    typedItem !== undefined &&
    typedItem.item_subtype === "PERSON" &&
    userPersonId === typedItem.id;
  const authState = combineLoadStates([readCheck, writeCheck]);
  // Only be true during the first loading,
  // not showing the loading spinner (and not removing the tab panel body component) when authentication is reloading
  const authStateInitalLoading =
    (readCheck.loading && !readCheck.success) ||
    (writeCheck.loading && !writeCheck.success);
  const loadingItem = typedLoading || untypedLoading || authStateInitalLoading;
  const fetchErrorOccurred = typedIsError || untypedIsError;
  const accessErrorOccurred = authState.error;
  const readAccessDeniedGlobal =
    readCheck.granted !== undefined && !readCheck.granted;
  const errorMessage =
    typedErrorMessage || untypedErrorMessage || authState.errorMessage;

  // Content
  const accessDeniedGlobalContent: JSX.Element = (
    <p>
      You do not have the correct roles to read from the Registry. You can
      manage your registry access roles at the{" "}
      <a href={LANDING_PAGE_LINK_PROFILE} target={"_blank"} rel="noreferrer">
        Landing Portal.
      </a>{" "}
      <br />
      For more information, visit{" "}
      <a href={requestingAccessLink} target="_blank" rel="noreferrer">
        our documentation
      </a>
      .
    </p>
  );
  const accessErrorContent: JSX.Element = (
    <p>
      An error occurred while determining user access. Error{" "}
      {errorMessage ?? "Unknown"}.
    </p>
  );
  const contains401 = errorMessage && errorMessage.includes("401");
  const fetchErrorContent: JSX.Element = (
    <p>
      An error occurred while fetching the item from the registry. Error{" "}
      {errorMessage ?? "Unknown"}.
      {contains401 && (
        <p>
          If you would like more information about accessing items in the
          registry see{" "}
          <a href={registryAccessLink} target="_blank" rel="noreferrer">
            our documentation
          </a>
          .
        </p>
      )}
    </p>
  );

  const historyErrorContent: JSX.Element = (
    <p>
      An error occurred while determining the history of the registry item.
      Please contact an administrator. Error: {historyErrorMessage ?? "Unknown"}
      .
    </p>
  );

  // You should be able to link study if model run and not linked to study
  const seeAddStudyLinkButton =
    isModelRun && !isLinkedToStudy && writeAccessGranted;

  // Use the add study link component to manage adding
  const studyLinkDialog = useAddStudyLinkDialog({
    modelRunId: handleId,
    onSuccess: () => {
      refetchLoadedItem();
    },
  });

  const { openDialog, renderedDialog } = useGenerateReportDialog({
    id: typedPayload?.item?.id, 
    itemSubType: typedPayload?.item?.item_subtype
  })

  return (
    <Grid container>
      {
        // Displays popup for version selector and revert op where relevant
      }
      {versionControls.render()}
      {revertControls.render()}
      {studyLinkDialog.render()}
      {renderedDialog}
      <Grid container item className={classes.topPanelContainer}>
        <Stack
          direction="row"
          justifyContent={"space-between"}
          alignItems={"center"}
          width={"100%"}
          className={classes.topPanel}
        >
          <div>
            {
              // Title and version group
            }
            <Stack
              direction="row"
              justifyContent="flex-start"
              spacing={2}
              alignItems="center"
              divider={
                <Divider
                  sx={{ bgcolor: "darkgrey" }}
                  orientation="vertical"
                  flexItem
                />
              }
            >
              <Typography variant="h5">Viewing {headerName} Record</Typography>
            </Stack>
          </div>
          <div>
            {
              // Buttons and lock display group RHS
            }
            <Stack
              direction="row"
              justifyContent={"flex-end"}
              spacing={2}
              alignItems={"center"}
            >
              {
                //Button group with possible multi column
              }
              <Grid
                container
                flexWrap="wrap"
                justifyContent="flex-end"
                alignItems="center"
                alignContent="center"
                rowGap={1}
                spacing={1}
              >
                {seeCloneButton && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      className={classes.actionButton}
                      href={`/cloneentity?id=${params.idPrefix}/${params.idSuffix}`}
                    >
                      Clone Entity
                    </Button>
                  </Grid>
                )}
                {seeMetadataUpdate && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      className={classes.actionButton}
                      href={`/editentity?id=${params.idPrefix}/${params.idSuffix}`}
                    >
                      Edit Entity
                    </Button>
                  </Grid>
                )}
                {isDataset && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      onClick={() => {
                        window.open(
                          datastoreLink,
                          "_blank",
                          "noopener,noreferrer"
                        );
                      }}
                    >
                      View In Datastore{" "}
                      <LaunchIcon style={{ marginLeft: "10px" }} />
                    </Button>
                  </Grid>
                )}

                {isModelRunOrStudy && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      onClick={openDialog}
                    >
                      Generate Report
                    </Button>
                  </Grid>
                )}

                {seeAddStudyLinkButton && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      onClick={() => {
                        // Start if possible
                        studyLinkDialog.startAddStudyLink &&
                          studyLinkDialog.startAddStudyLink();
                      }}
                    >
                      Link to Study
                    </Button>
                  </Grid>
                )}
                <Grid item>
                  <Button
                    variant="outlined"
                    className={classes.actionButton}
                    href={`${PROV_STORE_LINK}/record/view?rootId=${handleId}`}
                  >
                    Explore Lineage
                  </Button>
                </Grid>

                {item && (
                  <Grid item>
                    <Button
                      variant="outlined"
                      className={classes.actionButton}
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `https://hdl.handle.net/${item!.id}`
                        );
                        if (!handleCopied) {
                          setTimeout(() => {
                            setHandleCopied(false);
                          }, 2000);
                          setHandleCopied(true);
                        }
                      }}
                    >
                      Share Entity
                    </Button>

                    {handleCopied && (
                      <Chip
                        label="Handle copied!"
                        sx={{
                          backgroundColor: "green",
                          color: "white",
                          marginBottom: "12px",
                        }}
                      />
                    )}
                  </Grid>
                )}
              </Grid>
              {
                // If the resource is locked, show the lock icon
                locked && lockedResourceContent
              }
            </Stack>
          </div>
        </Stack>
      </Grid>
      <div className={classes.recordInfoPanel}>
        <Box
          sx={{
            borderBottom: 1,
            borderColor: "divider",
            marginBottom: "1em",
          }}
        >
          <Tabs
            value={desiredView}
            onChange={(e, value) => handleTabChange(value)}
          >
            <Tab
              label={"Overview"}
              value={overviewView}
              component={RouteLink}
              to={`/item/${handleId}?view=${overviewView}`}
            ></Tab>
            {
              // Versioning tab
            }
            {seeVersioning && (
              <Tab
                label={"Versioning"}
                value={versioningView}
                component={RouteLink}
                to={`/item/${handleId}?view=${versioningView}`}
              ></Tab>
            )}
            <Tab
              label={"Settings"}
              value={settingsView}
              component={RouteLink}
              to={`/item/${handleId}?view=${settingsView}`}
            ></Tab>
          </Tabs>
        </Box>
        <TabPanel index={overviewView} currentIndex={desiredView!}>
          {loadingItem ? (
            <CircularProgress />
          ) : readAccessDeniedGlobal ? (
            accessDeniedGlobalContent
          ) : fetchErrorOccurred ? (
            fetchErrorContent
          ) : historyError ? (
            historyErrorContent
          ) : accessErrorOccurred ? (
            accessErrorContent
          ) : (
            item && (
              <Grid container xs={12} spacing={2}>
                <Grid item className={classes.itemView}>
                  <ItemView
                    item={item!}
                    isUser={isUser}
                    locked={locked}
                    key={
                      // This makes sure that the component
                      // REMOUNTS if the history id is changed -
                      // otherwise we have essentially conditional
                      // hooks based on item contents
                      item!.id +
                      (
                        versionControls.state?.historyId ?? "noversion"
                      ).toString()
                    }
                  ></ItemView>
                </Grid>
                {workflowConfiguration.visible ? (
                  workflowViewExpanded ? (
                    <Grid item xs={4} className={classes.workflowView}>
                      <Box display="flex" alignItems="start">
                        <IconButton
                          aria-label="expand overflow view"
                          size="small"
                          onClick={() => {
                            setWorkflowViewExpanded(false);
                          }}
                        >
                          <React.Fragment>
                            <KeyboardArrowRight />
                            <Typography variant="body1">
                              Collapse Workflow
                            </Typography>
                          </React.Fragment>
                        </IconButton>
                      </Box>
                      <WorkflowVisualiserComponent
                        startingSessionID={
                          // Always defined as long as visible
                          workflowConfiguration.startingSessionId!
                        }
                        workflowDefinition={
                          // Always defined as long as visible
                          workflowConfiguration.workflowDefinition!
                        }
                        adminMode={workflowConfiguration.adminMode}
                        key={
                          workflowConfiguration.startingSessionId ??
                          "wfnokeyprovided"
                        }
                        direction="column"
                        enableExpand={false}
                      />
                    </Grid>
                  ) : (
                    <Box
                      display="flex"
                      alignItems="start"
                      paddingTop={2}
                      paddingLeft={2}
                    >
                      <IconButton
                        aria-label="expand overflow view"
                        size="small"
                        onClick={() => {
                          setWorkflowViewExpanded(true);
                        }}
                      >
                        <Icon
                          sx={{
                            alignSelf: "start",
                          }}
                        >
                          <KeyboardArrowLeft />
                        </Icon>

                        <Typography variant="body1">
                          <span>Expand</span>
                          <span>
                            <br />
                            Workflow
                          </span>
                        </Typography>
                      </IconButton>
                    </Box>
                  )
                ) : (
                  false
                )}
              </Grid>
            )
          )}
        </TabPanel>
        {seeVersioning && (
          <TabPanel index={versioningView} currentIndex={desiredView!}>
            {loadingItem ? (
              <CircularProgress />
            ) : readAccessDeniedGlobal ? (
              accessDeniedGlobalContent
            ) : fetchErrorOccurred ? (
              fetchErrorContent
            ) : historyError ? (
              historyErrorContent
            ) : accessErrorOccurred ? (
              accessErrorContent
            ) : (
              item && (
                <VersioningView
                  item={item!}
                  isAdmin={!!resourceAccess?.admin}
                  showSubtypeHeaderComponent={true}
                  isUser={isUser}
                  locked={locked}
                  lockedContent={lockedResourceContent}
                  versionIdLinkResolver={registryVersionIdLinkResolver}
                />
              )
            )}
          </TabPanel>
        )}
        <TabPanel index={settingsView} currentIndex={desiredView!}>
          {loadingItem ? (
            <CircularProgress />
          ) : fetchErrorOccurred ? (
            fetchErrorContent
          ) : accessErrorOccurred ? (
            accessErrorContent
          ) : (
            item &&
            subtype && (
              <Stack
                spacing={2}
                alignItems={"stretch"}
                divider={<Divider orientation="horizontal" flexItem />}
              >
                <MetadataHistory
                  hide={historyError}
                  locked={locked}
                  writeAccessGranted={writeAccessGranted}
                  isLatest={isLatest ?? true}
                  latestId={latestId}
                  versionControls={versionControls}
                  revertControls={revertControls}
                />
                {/* For Admin only */}
                {seeSettingsAdminRequiredContent && (
                  <AccessControl id={item.id} itemSubtype={subtype} />
                )}
                {seeSettingsAdminRequiredContent && (
                  <LockSettings
                    id={item.id}
                    subtype={subtype}
                    locked={locked}
                    setLocked={(locked) => {
                      setLocked(locked);
                    }}
                  />
                )}
              </Stack>
            )
          )}
        </TabPanel>
      </div>
    </Grid>
  );
});

export default RecordView;
