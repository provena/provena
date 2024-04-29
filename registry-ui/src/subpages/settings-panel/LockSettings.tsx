import React, { useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import LockIcon from "@mui/icons-material/Lock";
import { DataGrid, GridRowsProp, GridColDef } from "@mui/x-data-grid";
import {
  Button,
  Grid,
  Alert,
  Typography,
  Collapse,
  AlertTitle,
  TextField,
  Divider,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
} from "@mui/material";
import { action } from "mobx";
import lockStore from "../../stores/lockStore";
import {
  ItemSubType,
  LockEvent,
} from "../../provena-interfaces/RegistryModels";
import { timestampToLocalTime } from "react-libs";

interface LockStatusDisplayProps {
  locked: boolean;
}
const LockStatusDisplay = observer((props: LockStatusDisplayProps) => {
  /**
   * Component: LockStatusDisplay
   *
   */
  const color = props.locked ? "warning.main" : "success.main";

  return (
    <Grid
      container
      xs={12}
      alignItems={"center"}
      justifyContent={"space-evenly"}
    >
      <Grid item>
        <Typography color={color} variant="body1">
          This resource is <b>{props.locked ? "locked" : "unlocked"}</b>.
        </Typography>
      </Grid>
      {props.locked && <Grid item>{<LockIcon fontSize={"large"} />}</Grid>}
    </Grid>
  );
});

interface SuccessPopupProps {
  title: string;
  message: string;
  // It's state is controlled by a parent
  open: boolean;
}
const SuccessPopup = observer((props: SuccessPopupProps) => {
  /**
   * Component: SuccessPopup
   *
   */

  return (
    <Collapse in={props.open}>
      <Alert>
        <AlertTitle>{props.title}</AlertTitle>
        {props.message}
      </Alert>
    </Collapse>
  );
});

interface LockOrUnlockActionDisplayProps {
  //controlled
  locked: boolean;
  setLocked: (locked: boolean) => void;
  subtype: ItemSubType;
  id: string;
}
const LockOrUnlockActionDisplay = observer(
  (props: LockOrUnlockActionDisplayProps) => {
    /**
     * Component: LockOrUnlockActionDisplay
     *
     */
    const actionLoading =
      lockStore.lockAction.loading || lockStore.unlockAction.loading;
    const actionError =
      lockStore.lockAction.error || lockStore.unlockAction.error;
    const [errorMessage, setErrorMessage] = useState<string | undefined>(
      undefined,
    );

    // In progress of lock/unlock
    const [lodging, setLodging] = useState(false);
    const [reason, setReason] = useState<string | undefined>(undefined);

    // Success popup
    const [showingAlert, setShowingAlert] = useState<boolean>(false);
    const [alertMessage, setAlertMessage] = useState<string | undefined>(
      undefined,
    );
    const [alertTitle, setAlertTitle] = useState<string | undefined>(undefined);

    const swapLock = action(() => {
      props.setLocked(!props.locked);
    });

    // 3 seconds
    const alertDuration = 3000;

    const setupAlert = (message: string, title: string) => {
      setAlertMessage(message);
      setAlertTitle(title);
      setShowingAlert(true);
      setTimeout(() => {
        setShowingAlert(false);
      }, alertDuration);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      // enter key
      if (e.key === "Enter") {
        onActionSubmission();
      }
    };

    const onActionSubmission = props.locked
      ? () => {
          // We are locked, so let's unlock
          // Finished submitting
          setLodging(false);

          // Run the lock store unlock action
          lockStore
            .unlockResource(
              props.id,
              props.subtype,
              reason ?? "No reason provided.",
            )
            .then((res) => {
              swapLock();
              setupAlert("Successfully unlocked resource!", "Unlocked");
              lockStore.fetchLockHistory(props.id, props.subtype);
            })
            .catch((message) => {
              setErrorMessage(
                "Something went wrong when unlocking the resource, error: " +
                  message,
              );
            });
        }
      : () => {
          // We are unlocked, so let's lock
          setLodging(false);

          // Run the lock store lock action
          lockStore
            .lockResource(
              props.id,
              props.subtype,
              reason ?? "No reason provided.",
            )
            .then((res) => {
              swapLock();
              setupAlert("Successfully locked resource!", "Locked");
              lockStore.fetchLockHistory(props.id, props.subtype);
            })
            .catch((message) => {
              setErrorMessage(
                "Something went wrong when locking the resource, error: " +
                  message,
              );
            });
        };

    const onLockOrUnlockClick = () => {
      setLodging(true);
      // Reset any previous message
      setReason(undefined);
    };

    return (
      <Grid container xs={12} padding={0}>
        <Grid item xs={12}>
          <SuccessPopup
            message={alertMessage ?? ""}
            title={alertTitle ?? ""}
            open={showingAlert}
          ></SuccessPopup>
        </Grid>
        <Grid
          container
          xs={12}
          alignItems={"center"}
          spacing={2}
          justifyContent={"center"}
          padding={2}
        >
          {!showingAlert &&
            (actionLoading ? (
              <React.Fragment>
                <Grid item>Please wait...</Grid>
                <Grid item>
                  <CircularProgress />
                </Grid>
              </React.Fragment>
            ) : actionError ? (
              <React.Fragment>
                <Grid item>{errorMessage ?? "Unexpected error."}</Grid>
                <Grid item>
                  <Button
                    variant="contained"
                    color="warning"
                    onClick={() => {
                      lockStore.resetStore();
                    }}
                  >
                    {" "}
                    Dismiss error
                  </Button>
                </Grid>
              </React.Fragment>
            ) : lodging ? (
              <React.Fragment>
                <Grid container rowGap={2} xs={12}>
                  <Grid item xs={12}>
                    Please provide a reason for
                    <b>{props.locked ? " unlocking " : " locking "}</b>
                    this resource:
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      value={reason}
                      onChange={(change) => {
                        setReason(change.target.value);
                      }}
                      onKeyDown={handleKeyDown}
                      label={"Enter a short justification here"}
                      placeholder={"Your reason"}
                      fullWidth
                    ></TextField>
                  </Grid>
                  <Grid
                    container
                    xs={12}
                    alignItems={"center"}
                    justifyContent={"space-evenly"}
                  >
                    <Grid item>
                      <Button
                        color="warning"
                        variant="contained"
                        onClick={() => setLodging(false)}
                      >
                        Cancel
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button
                        color="success"
                        variant="contained"
                        onClick={onActionSubmission}
                      >
                        Submit
                      </Button>
                    </Grid>
                  </Grid>
                </Grid>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <Grid item>
                  Click here to {props.locked ? "unlock" : "lock"} the resource
                </Grid>
                <Grid item>
                  <Button variant="contained" onClick={onLockOrUnlockClick}>
                    {props.locked ? "Unlock the resource" : "Lock the resource"}
                  </Button>
                </Grid>
              </React.Fragment>
            ))}
        </Grid>
      </Grid>
    );
  },
);

interface DataGridHistoryItem {
  id: string;
  action_type: string;
  actor_email: string;
  reason: string;
  datetime: string;
}

interface LockHistoryTableProps {
  lockHistory: LockEvent[];
}
const LockHistoryTable = observer((props: LockHistoryTableProps) => {
  /**
   * Component: LockHistoryTable
   *
   */
  const defaultRowsPerPage = 10;
  const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);
  const tableHeight = 500;
  const rows: GridRowsProp = props.lockHistory
    // Make a standard interface from group items and pull out
    // membership
    .map((lockEvent) => {
      return {
        // create unique string id combination
        id:
          lockEvent.timestamp.toString() +
          lockEvent.username +
          lockEvent.action_type,
        action_type: lockEvent.action_type,
        actor_email: lockEvent.email,
        reason: lockEvent.reason,
        datetime: timestampToLocalTime(lockEvent.timestamp),
      } as DataGridHistoryItem;
    })
    .reverse();
  const columns: GridColDef[] = [
    { field: "action_type", headerName: "Action", flex: 0.1 },
    { field: "actor_email", headerName: "Email", flex: 0.2 },
    { field: "reason", headerName: "Reason", flex: 0.55 },
    { field: "datetime", headerName: "Timestamp", flex: 0.15 },
  ];

  // This shouldn't occur since we don't run the dialog unless there is
  // history, but here as a catch all
  if (rows.length === 0) {
    return <div>This resource has no lock history.</div>;
  }

  return (
    <div style={{ height: tableHeight, width: "100%" }}>
      <DataGrid
        pageSize={pageSize}
        rowsPerPageOptions={[5, 10, 20]}
        onPageSizeChange={(size) => {
          setPageSize(size);
        }}
        columns={columns}
        rows={rows}
      ></DataGrid>
    </div>
  );
});

interface LockHistoryDisplayProps {
  lockHistory: Array<LockEvent> | undefined;
}

const LockHistoryDisplay = observer((props: LockHistoryDisplayProps) => {
  /**
   * Component: LockHistoryDisplay
   */

  const [showingHistory, setShowingHistory] = useState(false);
  const hasHistory = props.lockHistory && props.lockHistory.length > 0;

  const launchTable = () => {
    setShowingHistory(true);
  };
  const closeTable = () => {
    setShowingHistory(false);
  };

  const headerContent: JSX.Element = (
    <React.Fragment>
      <Grid item>
        <h3>Lock History</h3>
      </Grid>
      {!showingHistory && hasHistory && (
        <Grid item>
          <Button variant={"contained"} onClick={launchTable}>
            Show history
          </Button>
        </Grid>
      )}
      <Grid item xs={12}>
        Whenever a resource is locked or unlocked, this information is recorded.{" "}
        {!hasHistory && (
          <b>
            <i> This resource has no history to display.</i>
          </b>
        )}
      </Grid>
    </React.Fragment>
  );

  var bodyContent: JSX.Element = <React.Fragment></React.Fragment>;

  if (showingHistory) {
    // undefined case
    if (props.lockHistory === undefined) {
      bodyContent = (
        <React.Fragment>
          <Grid item xs={12}>
            No content is available in the lock history. If this seems wrong,
            please contact an admin.
          </Grid>
        </React.Fragment>
      );
    }
    // History present case
    else {
      bodyContent = (
        <React.Fragment>
          <Dialog
            open={showingHistory}
            onClose={closeTable}
            fullWidth={true}
            maxWidth={"lg"}
          >
            <DialogTitle>
              <Grid
                container
                alignItems={"center"}
                justifyContent={"space-between"}
              >
                <Grid item>Lock event history</Grid>
                <Grid item>
                  <DialogActions>
                    <Button onClick={closeTable}>Close</Button>
                  </DialogActions>
                </Grid>
              </Grid>
            </DialogTitle>
            <DialogContent>
              <LockHistoryTable
                lockHistory={props.lockHistory}
              ></LockHistoryTable>
            </DialogContent>
          </Dialog>
        </React.Fragment>
      );
    }
  }

  return (
    <Grid
      container
      xs={12}
      alignItems={"center"}
      justifyContent={"flex-start"}
      spacing={2}
      rowGap={1}
    >
      {headerContent}
      {bodyContent}
    </Grid>
  );
});

export interface LockSettingsProps {
  id: string;
  subtype: ItemSubType;
  locked: boolean;
  setLocked: (locked: boolean) => void;
}

export const LockSettings = observer((props: LockSettingsProps) => {
  /**
   * Component: LockSettings
   *
   */
  const [expanded, setExpanded] = useState(false);
  const handle = props.id;

  // Load the lock history to display history panel
  useEffect(() => {
    lockStore.fetchLockHistory(handle, props.subtype);
  }, [handle]);

  const headerContent: JSX.Element = (
    <React.Fragment>
      <Grid
        container
        alignItems={"center"}
        justifyContent={"flex-start"}
        spacing={2}
        padding={0}
      >
        <Grid item>
          <h2>Lock Settings</h2>
        </Grid>
        <Grid item>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? (
              <React.Fragment>
                <KeyboardArrowDownIcon /> Collapse
              </React.Fragment>
            ) : (
              <React.Fragment>
                <KeyboardArrowRightIcon /> Expand
              </React.Fragment>
            )}
          </IconButton>
        </Grid>
        <Grid item xs={12}>
          As an administrator of this resource, you are able to apply or remove
          a <i>lock</i> which stops users from making any changes to the data or
          metadata of the resource. {!expanded && "Expand to see more"}
        </Grid>
      </Grid>
    </React.Fragment>
  );

  var bodyContent: JSX.Element = <React.Fragment></React.Fragment>;

  if (expanded) {
    bodyContent = (
      <Grid container rowGap={1.5} alignItems="center">
        <Grid item xs={12}>
          <Divider />
        </Grid>
        <Grid item xs={5}>
          <LockStatusDisplay locked={props.locked}></LockStatusDisplay>
        </Grid>
        <Grid item xs={7}>
          <LockOrUnlockActionDisplay
            locked={props.locked}
            setLocked={props.setLocked}
            subtype={props.subtype}
            id={props.id}
          ></LockOrUnlockActionDisplay>
        </Grid>
        <Grid item xs={12}>
          <Divider />
        </Grid>
        {lockStore.historyAction.ready() ? (
          <Grid item xs={12}>
            <LockHistoryDisplay
              lockHistory={lockStore.historyAction.content?.history}
            ></LockHistoryDisplay>
          </Grid>
        ) : (
          <Grid item xs={12}>
            <CircularProgress />
          </Grid>
        )}
      </Grid>
    );
  }

  return (
    <Stack>
      {headerContent}
      {bodyContent}
    </Stack>
  );
});
