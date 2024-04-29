import { Button, Stack, Typography } from "@mui/material";
import { Alert, AlertTitle, CircularProgress } from "@mui/material";
import { useValidateAndAssignLink } from "react-libs";

interface AlertConfig {
  severity: "info" | "warning" | "error" | "success";
  title: string | JSX.Element;
  body: JSX.Element | null;
}
interface ValidateAssignComponentComponentProps {
  personId: string;
  onAssignment: () => void;
}
const ValidateAssignComponentComponent = (
  props: ValidateAssignComponentComponentProps
) => {
  /**
    Component: ValidateAssignComponentComponent

    Manages the Person linking validation, submission and result displays
    (including error catches) for the validate/submit workflow.

    Displays as a varying alert depending on status.

    When successful, runs the on assignment callback.

    User can clear from this tool through the on clear callback.
    */
  const assignAndValidate = useValidateAndAssignLink({
    personId: props.personId,
    onAssignmentSuccess: props.onAssignment,
  });

  // Unpack some state from custom hook
  const validationLoading = assignAndValidate.validationResult?.loading ?? true;

  const submissionLoading =
    assignAndValidate.submissionResult?.loading ?? false;

  var validationAlertConfig: AlertConfig = {
    severity: "info",
    title: "Please wait...",
    body: <p>Please wait</p>,
  };

  const centeredLoad = (
    <Stack direction="row" justifyContent="center">
      <CircularProgress />
    </Stack>
  );

  // Check states and display suitable alert status

  // Validation in progress
  if (validationLoading) {
    validationAlertConfig = {
      severity: "info",
      title: "Validating selection, please wait...",
      body: centeredLoad,
    };
  }
  // Submission in progress
  else if (submissionLoading) {
    validationAlertConfig = {
      severity: "info",
      title: "Submitting Person assignment, please wait...",
      body: centeredLoad,
    };
  }
  // Submission completed success
  else if (!!assignAndValidate.submissionResult?.success) {
    validationAlertConfig = {
      severity: "success",
      title: "Succesfully linked Person identity",
      body: (
        <p>
          The selected Person ({props.personId}) was linked to your account. If
          you need to update or clear this assignment, please contact a system
          administrator.{" "}
        </p>
      ),
    };
  }
  // Submission completed error
  else if (!!assignAndValidate.submissionResult?.error) {
    validationAlertConfig = {
      severity: "error",
      title: "An error occurred while linking to the specified Person",
      body: (
        <p>
          An error occurred while linking the selected Person ({props.personId})
          to your account. Error details:{" "}
          {assignAndValidate.submissionResult?.errorMessage ?? "Unknown error."}
          . Please try refreshing and repeating the process. If the issue
          persists, contact a system administrator.
        </p>
      ),
    };
  }
  // Validation success - awaiting action
  else if (!!assignAndValidate.valid) {
    validationAlertConfig = {
      severity: "success",
      title: "Selected Person is valid for assignment",
      body: (
        <Stack direction="column" spacing={2}>
          <p>
            The selected Person is valid for assignment. By selecting "Assign to
            me" you are specifying that the selected person is you. Actions
            performed by this account will be linked to this Person. You cannot
            undo this action.
          </p>
          <Stack
            direction="row"
            justifyContent="center"
            paddingLeft={1}
            paddingRight={1}
            alignItems="center"
          >
            {
              // Submit
            }
            <Button
              variant="outlined"
              color="success"
              disabled={assignAndValidate.submit === undefined}
              onClick={assignAndValidate.submit ?? (() => {})}
            >
              Assign to me
            </Button>
          </Stack>
        </Stack>
      ),
    };
  }
  // Validation failed - report issue
  else if (assignAndValidate.valid !== undefined && !assignAndValidate.valid) {
    validationAlertConfig = {
      severity: "error",
      title: "Selected Person is not valid for assignment",
      body: (
        <p>
          A validation error occurred when verifying this Person as a candidate
          for assignment. Details:{" "}
          {assignAndValidate.validationResult?.data?.status.details ??
            "Unknown."}{" "}
          Try refreshing and trying the process again. Otherwise, contact an
          administrator if this error appears incorrect.
        </p>
      ),
    };
  }
  // Validation failed (from API issue i.e. Non 200OK issue)
  else if (!!assignAndValidate.validationResult?.error) {
    validationAlertConfig = {
      severity: "error",
      title: "An error occurred while validating the selection",
      body: (
        <p>
          An unexpected validation error occurred when verifying this Person as
          a candidate for assignment. Details:{" "}
          {assignAndValidate.validationResult?.errorMessage ?? "Unknown error."}{" "}
          Try refreshing and trying the process again. Otherwise, contact an
          administrator if this error appears incorrect.
        </p>
      ),
    };
  }

  const currentAlert = (
    <Alert
      severity={validationAlertConfig.severity}
      variant="outlined"
      // Force max width
      style={{ width: "100%" }}
    >
      <Stack direction="column" spacing={2} justifyContent="flex-start">
        <AlertTitle>{validationAlertConfig.title}</AlertTitle>
        {validationAlertConfig.body}
      </Stack>
    </Alert>
  );

  return (
    <Stack direction="column" spacing={1}>
      <Typography variant="h6">
        Assign selected Person ({props.personId})
      </Typography>
      {
        // validation section
      }
      {currentAlert}
    </Stack>
  );
};

interface LinkPersonBoxComponentProps {
  person_id: string;
}
export const LinkPersonBoxComponent = (props: LinkPersonBoxComponentProps) => {
  /**
    Component: LinkPersonBoxComponent

    This component allows the user to link their person if applicable. 

    Firstly runs a validity check, then allows user to submit if desired.
    
  */

  // TODO Destub

  // Manage state for check

  // Manage state for submission

  const onSubmit = () => {
    // TODO destub
  };

  return (
    <div>
      <Stack spacing={2}>
        <Typography variant="h4">
          Would you like to link this Person to your user account?
        </Typography>
        <Typography variant="body1">
          You have successfully registered a new Person. If this Person is
          intended to represent you, you can link it to your user.
        </Typography>
        <ValidateAssignComponentComponent
          onAssignment={() => {}}
          personId={props.person_id}
        ></ValidateAssignComponentComponent>
      </Stack>
    </div>
  );
};
