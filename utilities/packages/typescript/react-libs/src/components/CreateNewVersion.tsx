import {
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Dialog,
  Grid,
  Stack,
  TextField,
  Theme,
  Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import React, { useEffect, useRef, useState } from "react";
import { useHistory } from "react-router-dom";
import { useCreateNewVersion } from "../hooks/useCreateNewVersion";
import { ItemBase, VersionResponse } from "../provena-interfaces/RegistryAPI";
import { isBlank } from "../util";
import { GenericDetailViewWrapperComponent } from "./JsonRenderer";
import { DOCUMENTATION_BASE_URL } from "../queries";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: "100%",
      borderRadius: 5,
    },
    dialogContent: {
      display: "flex",
      flexWrap: "wrap",
      overflowY: "hidden",
      overflowX: "hidden",
      height: "100%",
      width: "100%",
      padding: theme.spacing(4),
    },
    dialogDescription: {
      width: "100%",
    },
    versionReason: {
      width: "100%",
    },
    button: {
      width: "100%",
      justifyContent: "space-evenly",
    },
    tbPaddings: {
      paddingTop: theme.spacing(2),
      paddingBottom: theme.spacing(2),
    },
    fullWidth: { width: "100%" },
  }),
);

interface CreateNewVersionProps {
  item: ItemBase;
  open: boolean;
  setOpenInParent: (openInParent: boolean) => void;
  // Path for jumping between item's tabs, used for registry or datastore
  versionIdLinkResolver: (id: string) => string;
}

const CreateNewVersion = (props: CreateNewVersionProps) => {
  /**
    Component: CreateNewVersion

    A dialog for create a new version
    */

  const classes = useStyles();

  const [validInput, setValidInput] = useState<boolean>(true);

  // Version reason
  const [reason, setReason] = useState<string>("");

  // For refreshing page after successfully submitted.
  const history = useHistory();

  // Set mutation for submitting
  const createNewVersionMutate = useCreateNewVersion({});

  // Save timer for cleaning
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Clean up
  useEffect(() => {
    return () => handleClose();
  }, []);

  // Documentation for providing information on creating new version
  const CREATE_NEW_VERSION_HELP_LINK = DOCUMENTATION_BASE_URL + "/versioning/";

  // States
  const isSubmitting = createNewVersionMutate.isLoading;
  const isSuccess = createNewVersionMutate.isSuccess;
  const isError = createNewVersionMutate.isError;

  // Handler

  const handleClose = () => {
    // Clear timer
    if (timer.current) {
      clearTimeout(timer.current);
    }
    // Close dialog window
    props.setOpenInParent(false);
  };

  const textFieldOnChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const currentTextValue: string = e.target.value;
    setReason(currentTextValue);
  };

  const handleOnSuccess = (data: VersionResponse) => {
    const newVersionId = data.new_version_id;
    const versioningView = "versioning";
    // Set redirect path when submit successfully
    if (!!newVersionId) {
      const delayForRedirect: number = 5000;
      timer.current = setTimeout(() => {
        history.push(props.versionIdLinkResolver(newVersionId));
        handleClose();
      }, delayForRedirect);
    } else {
      // In case some issues happen on new version id, just refresh current page
      history.go(0);
      handleClose();
    }
  };

  const handleSubmit = (e: React.SyntheticEvent) => {
    // Handle submit
    // Prevent the browser from reloading the page
    e.preventDefault();

    if (!isBlank(reason)) {
      // Submit
      createNewVersionMutate.mutate(
        {
          item: props.item,
          reason,
        },
        {
          onSuccess: (data) => {
            handleOnSuccess(data);
          },
        },
      );
    } else {
      // Input version reason is empty
      // Show empty input alert
      setValidInput(false);
    }
  };

  return (
    <>
      {props.open && (
        <Dialog
          open={props.open}
          className={classes.root}
          fullWidth
          maxWidth="md"
        >
          {isSuccess ? (
            // If successfully created a new version, jump to this content
            <Grid container className={classes.dialogContent}>
              <Stack direction="column" className={classes.fullWidth}>
                <Alert
                  variant="outlined"
                  severity="success"
                  className={classes.fullWidth}
                >
                  <AlertTitle>
                    Success: New version submitted successfully.
                  </AlertTitle>
                </Alert>
                {/* Show new version info */}
                <Stack
                  direction="column"
                  className={classes.fullWidth}
                  rowGap={2}
                  pt={2}
                >
                  <Typography variant="h6">New version create:</Typography>
                  <GenericDetailViewWrapperComponent
                    item={{
                      id: createNewVersionMutate.data.new_version_id,
                      "Session id":
                        createNewVersionMutate.data.version_job_session_id,
                    }}
                    layout={"column"}
                  />
                  <Typography variant="body1">
                    You will be redirected to the newest version in a few
                    seconds...
                  </Typography>
                </Stack>
              </Stack>
            </Grid>
          ) : (
            <Grid container className={classes.dialogContent}>
              <Grid item xs={12}>
                <Typography variant="h5">Create a new version</Typography>
              </Grid>
              <Grid item>
                <Typography
                  variant="body1"
                  className={`${classes.dialogDescription} ${classes.tbPaddings}`}
                >
                  Create a new version of the current item. Click{" "}
                  <span>
                    <a
                      href={CREATE_NEW_VERSION_HELP_LINK}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      here
                    </a>
                  </span>{" "}
                  to learn more.
                </Typography>
              </Grid>
              {/* Create new version form */}
              <Grid container item>
                <form onSubmit={handleSubmit} className={classes.versionReason}>
                  {/* Version reason */}
                  <TextField
                    required={true}
                    error={!validInput}
                    name="versionReason"
                    label="Version Reason"
                    placeholder="Please enter an explanation of why a new version is required."
                    multiline
                    fullWidth
                    variant="outlined"
                    rows={8}
                    disabled={isSubmitting || isSuccess}
                    className={classes.versionReason}
                    onInvalid={(e) =>
                      (e.target as HTMLInputElement).setCustomValidity(
                        "Please complete this field, you must provide a reason for creating this version.",
                      )
                    }
                    onInput={(e) => {
                      (e.target as HTMLInputElement).setCustomValidity("");
                      setValidInput(true);
                    }}
                    onChange={textFieldOnChange}
                  />
                  {/* Handling buttons */}
                  <Grid
                    container
                    item
                    xs={12}
                    className={`${classes.button} ${classes.tbPaddings}`}
                  >
                    <Grid item>
                      <Button
                        variant="contained"
                        type="button"
                        onClick={handleClose}
                        disabled={isSubmitting}
                      >
                        {isSuccess ? "Close" : "Cancel"}
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button
                        variant="contained"
                        type="submit"
                        disabled={isSubmitting || isSuccess}
                      >
                        Submit
                      </Button>
                    </Grid>
                  </Grid>
                  {/* Handling empty input string error alert */}
                  {!validInput && (
                    <Grid item xs={12}>
                      <Alert
                        variant="outlined"
                        severity="warning"
                        className={classes.fullWidth}
                      >
                        <AlertTitle>Alert</AlertTitle>
                        Version Reason cannot be empty. Please complete the
                        Version Reason field above, you must provide a reason
                        for creating this version.
                      </Alert>
                    </Grid>
                  )}
                </form>
              </Grid>
              <Grid item xs={12}>
                {isSubmitting && (
                  <Stack direction="row" className={classes.fullWidth}>
                    <CircularProgress />
                    <Typography variant="body1" paddingLeft={2} paddingTop={2}>
                      Creating new version...
                    </Typography>
                  </Stack>
                )}
                {isError && (
                  <Alert
                    variant="outlined"
                    severity="error"
                    className={classes.fullWidth}
                  >
                    <AlertTitle>
                      Error: An error occurred when submitting new version:
                    </AlertTitle>
                    {createNewVersionMutate.error ?? "Unknown."}
                  </Alert>
                )}
              </Grid>
            </Grid>
          )}
        </Dialog>
      )}
    </>
  );
};

export default CreateNewVersion;
