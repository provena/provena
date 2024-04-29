import {
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Dialog,
  Divider,
  FormControl,
  Grid,
  Stack,
  TextField,
  Theme,
  Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useApprovalAction } from "hooks/useApprovalAction";
import { useEffect, useRef, useState } from "react";
import {
  GenericDetailViewWrapperComponent,
  RenderLongTextExpand,
  useTypedLoadedItem,
} from "react-libs";
import {
  ItemDataset,
  ItemSubType,
  ReleaseAction,
} from "react-libs/provena-interfaces/RegistryAPI";
import { useHistory, useParams } from "react-router-dom";
import { datasetApprovalsTabLinkResolver } from "util/helper";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      padding: theme.spacing(4),
      borderRadius: 5,
      backgroundColor: theme.palette.common.white,
      width: "100%",
      minHeight: "80vh",
    },
    actionButtons: {
      width: "100%",
      justifyContent: "center",
    },
    // Success dialog
    successDialog: {
      borderRadius: 5,
      width: "100%",
    },
    // Other useful layout
    fullWidth: { width: "100%" },
    tbPaddings: {
      paddingTop: theme.spacing(2),
      paddingBottom: theme.spacing(2),
    },
    lrPadding: {
      paddingLeft: theme.spacing(2),
      paddingRight: theme.spacing(2),
    },
  }),
);

interface ApprovalActionParams {
  id: string;
  dataset_approver: string;
}

export const ApprovalAction = () => {
  /**
    Component: ApprovalAction

    The action taken page when approver clicked take action for approval
    */

  const classes = useStyles();

  const history = useHistory();

  // Dataset id
  const { id: dataset_id } = useParams<ApprovalActionParams>();

  // Approver note
  const [approverNote, setApproverNote] = useState<string>("");

  // Approver action
  const [approved, setApproved] = useState<boolean>();

  // Dialog open when submit successfully
  const [successDialogOpen, setSuccessDialogOpen] = useState<boolean>(false);

  // Save dialog timeout timer for cleaning
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Load dataset information for displaying
  const loadedDataset = useTypedLoadedItem({
    enabled: true,
    id: dataset_id,
    subtype: "DATASET" as ItemSubType,
  });
  const dataset = loadedDataset.data?.item as ItemDataset;

  // use mutate to take approval action
  const approvalAction = useApprovalAction();

  // Cleaning
  useEffect(() => {
    return () => handleClean();
  }, []);

  // Status
  if (loadedDataset.loading) {
    return (
      <Stack direction="column" className={classes.root} spacing={2}>
        <CircularProgress />
      </Stack>
    );
  }

  if (loadedDataset.error) {
    return (
      <Stack direction="column" className={classes.root} spacing={2}>
        <Alert variant="outlined" severity="error">
          <AlertTitle>
            Error: An error occurred when fetching the dataset.
          </AlertTitle>
          {loadedDataset.errorMessage ?? "Error message is not provided."}
        </Alert>
      </Stack>
    );
  }

  // Set values for displaying

  // Get the latest history info
  const lastReleaseHistory =
    !!dataset.release_history && dataset.release_history.length !== 0
      ? dataset.release_history[dataset.release_history.length - 1]
      : undefined;

  // requester
  const requesterId = !!lastReleaseHistory
    ? lastReleaseHistory.requester
    : undefined;

  // Requester note
  const requesterNote =
    !!lastReleaseHistory &&
    lastReleaseHistory.action === ("REQUEST" as ReleaseAction)
      ? !!lastReleaseHistory.notes
        ? lastReleaseHistory.notes
        : "No note has been provided by the requester."
      : "Last approval request information was not found.";

  // Handler

  // For save approver's note
  const textFieldOnChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    event.preventDefault();
    const approverNote = event.target.value;
    setApproverNote(approverNote);
  };

  // onSuccess
  const handleOnSuccess = () => {
    const delayForRedirect: number = 4000;
    // Open success dialog
    setSuccessDialogOpen(true);
    // Set timer for redirect
    timer.current = setTimeout(() => {
      handleRedirect();
    }, delayForRedirect);
  };

  // Submit approval action
  const handleSubmit = (event: React.SyntheticEvent) => {
    event.preventDefault();
    if (approved !== undefined) {
      approvalAction.mutate(
        {
          datasetId: dataset_id,
          approve: approved,
          approverNote: approverNote,
        },
        { onSuccess: handleOnSuccess },
      );
    }
  };

  // Close, and redirect to dataset's overview tab
  const handleRedirect = () => {
    const desiredLink = datasetApprovalsTabLinkResolver(dataset_id);
    history.push(desiredLink);
  };

  // Cleaning functions before closing
  const handleClean = () => {
    // Clear timer
    if (timer.current) {
      clearTimeout(timer.current);
    }
    // Close dialog window
    setSuccessDialogOpen(false);
  };

  // Status

  // Latest history error
  const errorOccurredFindingRequester =
    !lastReleaseHistory ||
    !requesterId ||
    lastReleaseHistory.action !== ("REQUEST" as ReleaseAction);

  // Submit approval action
  const isSubmitting = approvalAction.isLoading;
  const isSuccess = approvalAction.isSuccess;
  const isError = approvalAction.isError;

  return (
    <Stack
      direction="column"
      className={classes.root}
      spacing={4}
      divider={<Divider orientation="horizontal" flexItem />}
    >
      <Typography variant="h4">Take Action for Approval</Typography>
      {/* Show dataset information */}
      <Stack direction="column" className={classes.fullWidth} spacing={4}>
        <Typography variant="h6">
          <strong>Dataset Details:</strong>
        </Typography>
        <GenericDetailViewWrapperComponent
          item={{ dataset_id: dataset_id }}
          layout={"column"}
        />
      </Stack>
      {/* Show requester information */}
      <Stack direction="column" className={classes.fullWidth} spacing={4}>
        <Typography variant="h6">
          <strong>Requester Details:</strong>
        </Typography>
        {errorOccurredFindingRequester ? (
          <Stack direction="column" className={classes.fullWidth}>
            <Alert variant="outlined" severity="error">
              <AlertTitle>
                Error: An error occurred when fetching requester's information.
              </AlertTitle>
              Requester information cannot be found in the dataset's release
              history.
            </Alert>
          </Stack>
        ) : (
          <GenericDetailViewWrapperComponent
            item={{ linked_person_id: requesterId }}
            layout={"column"}
          />
        )}
      </Stack>
      {/* Show requester note */}
      <Stack direction="column" className={classes.fullWidth} spacing={4}>
        <Typography variant="h6">
          <strong>Requester Note:</strong>
        </Typography>
        <RenderLongTextExpand text={requesterNote} initialCharNum={500} />
      </Stack>
      {/* Form */}
      <form onSubmit={handleSubmit}>
        <Stack direction="column" spacing={4}>
          {/* Description */}
          <Typography variant="h5">
            Please review and take action on the current approval request:
          </Typography>
          {/* Approver notes */}
          <Stack>
            <TextField
              name="approverNote"
              label="Notes to requester"
              placeholder="Please enter any notes to requester..."
              multiline
              fullWidth
              variant="outlined"
              rows={12}
              disabled={isSubmitting || isSuccess}
              onChange={textFieldOnChange}
            />
          </Stack>
          {/* Action buttons */}
          <Grid container xs={12} className={classes.fullWidth}>
            <Grid container item xs={6} className={classes.actionButtons}>
              <Button
                variant="contained"
                type="button"
                onClick={handleRedirect}
                disabled={isSubmitting || isSuccess}
              >
                Close
              </Button>
            </Grid>
            <Grid container item xs={6} className={classes.actionButtons}>
              <Grid item className={classes.lrPadding}>
                <Button
                  variant="contained"
                  color="error"
                  type="submit"
                  disabled={isSubmitting || isSuccess}
                  onClick={() => setApproved(false)}
                >
                  Reject
                </Button>
              </Grid>
              <Grid item className={classes.lrPadding}>
                <Button
                  variant="contained"
                  color="success"
                  type="submit"
                  disabled={isSubmitting || isSuccess}
                  onClick={() => setApproved(true)}
                >
                  Approve
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </Stack>
      </form>
      {/* Submitting */}
      {isSubmitting && <CircularProgress />}
      {/* Success and redirect */}
      {successDialogOpen && (
        <Dialog
          open={successDialogOpen}
          className={classes.successDialog}
          fullWidth
          maxWidth="md"
        >
          <Stack direction="column" className={classes.fullWidth} p={4}>
            <Alert variant="outlined" severity="success">
              <AlertTitle>
                Success: Your approval action has been submitted successfully.
              </AlertTitle>
              You will be redirected to the dataset's approvals tab in a few
              seconds...
            </Alert>
          </Stack>
        </Dialog>
      )}
      {/* Error */}
      {isError && (
        <Stack
          direction="column"
          className={`${classes.fullWidth} ${classes.tbPaddings}`}
        >
          <Alert variant="outlined" severity="error">
            <AlertTitle>
              Error: An error occurred when submitting the approval action.
            </AlertTitle>
            {approvalAction.error ?? "Error message not provided."}
          </Alert>
        </Stack>
      )}
    </Stack>
  );
};
