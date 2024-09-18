import {
  Alert,
  AlertTitle,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { stripPossibleFullStop, SubtypeSearchSelector } from "react-libs";
import { AddStudyLinkResponse } from "react-libs/provena-interfaces/AsyncJobAPI";
import { useAddStudyLink } from "./useAddStudyLink";

export interface UseAddStudyLinkDialogProps {
  // What is the ID of the model run?
  modelRunId: string | undefined;

  // Optional hook for when the revert is completed successfully
  onSuccess?: (response: AddStudyLinkResponse) => void;
}
export interface UseAddStudyLinkDialogOutput {
  // Only available if data is provided
  startAddStudyLink?: () => void;
  // Renders the JSX element (dialog box)
  render: () => JSX.Element | null;
}
export const useAddStudyLinkDialog = (
  props: UseAddStudyLinkDialogProps
): UseAddStudyLinkDialogOutput => {
  /**
    Hook: useAddStudyLinkDialog
    
    Manages a dialog popup to submit an add study link operation.
    */

  // Is the popup active?
  const [popupOpen, setPopupOpen] = useState<boolean>(false);
  const [studyId, setStudyId] = useState<string | undefined>(undefined);

  // On submit handler
  const onSubmit = () => {
    if (addStudyLinkOp.dataReady) {
      if (addStudyLinkOp.submit !== undefined) {
        addStudyLinkOp.submit();
      }
    }
  };

  // Manage the revert API ops
  const addStudyLinkOp = useAddStudyLink({
    studyId: studyId,
    modelRunId: props.modelRunId,
    onSuccess: (res) => {
      // Run the props on success if provided
      if (props.onSuccess !== undefined) {
        props.onSuccess(res);
      }
      // Always close the popup when succeeded
      setPopupOpen(false);
    },
  });

  // Default render option returns null - still safe to include in JSX
  var render: () => JSX.Element | null = () => {
    return null;
  };

  // Alternative states
  const loading = !!addStudyLinkOp.response?.loading;
  const error = !!addStudyLinkOp.response?.error;
  const errorMessage = addStudyLinkOp.response?.errorMessage;

  const submitDisabled = !addStudyLinkOp.dataReady || loading;

  if (popupOpen) {
    render = () => {
      return (
        <Dialog
          open={popupOpen}
          onClose={() => {
            setPopupOpen(false);
          }}
          fullWidth={true}
          maxWidth={"md"}
        >
          <DialogContent>
            <Stack spacing={2} direction="column">
              <SubtypeSearchSelector
                description="Link an existing model run to a study in the registry by searching or entering a valid ID."
                subtypePlural="Studies"
                required={true}
                selectedId={studyId}
                setSelectedId={setStudyId}
                subtype="STUDY"
                title="Select a Study"
                persistTitle={true}
              />
              {error && (
                <Alert severity="error" variant="outlined">
                  <AlertTitle>An error occurred</AlertTitle>
                  <Typography variant="subtitle1">
                    An error occurred while running the link operation. Error:{" "}
                    {errorMessage
                      ? stripPossibleFullStop(errorMessage)
                      : "Unknown"}
                    . Try refreshing the page and performing the operation
                    again, or contact an administrator for assistance.
                  </Typography>
                </Alert>
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button
              disabled={loading}
              onClick={() => {
                setPopupOpen(false);
              }}
            >
              Cancel
            </Button>
            <Button
              color="success"
              disabled={submitDisabled}
              onClick={onSubmit}
            >
              Submit
            </Button>
          </DialogActions>
        </Dialog>
      );
    };
  }
  return {
    render,
    startAddStudyLink: () => {
      setStudyId(undefined);
      setPopupOpen(true);
    },
  };
};
