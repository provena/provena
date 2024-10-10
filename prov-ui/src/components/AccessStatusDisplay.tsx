import { Alert, AlertTitle, CircularProgress, Stack } from "@mui/material";
import { useAccessCheck } from "react-libs";

export interface AccessStatusDisplayComponentProps {
  accessCheck: ReturnType<typeof useAccessCheck>;
}
export const AccessStatusDisplayComponent = (
  props: AccessStatusDisplayComponentProps
) => {
  /**
    Component: AccessStatusDisplayComponent

    Displays the loading/status of the access check - only used in the case that
    access is not yet granted
    */
  const status = props.accessCheck;
  var content: JSX.Element = <p></p>;

  if (status.loading) {
    content = (
      <Stack justifyContent="center" direction="row">
        <CircularProgress />;
      </Stack>
    );
  } else if (status.error) {
    content = (
      <Alert severity={"error"}>
        <AlertTitle>Error</AlertTitle>
        <p>
          {" "}
          An error occurred while retrieving access information. Error:{" "}
          {status.errorMessage ?? "Unknown"}. <br />
          If you cannot determine how to fix this issue, try refreshing, or
          contact us to get help.
        </p>
      </Alert>
    );
  } else if (!status.error && !status.loading && !status.granted) {
    content = <p>Access not granted</p>;
  } else {
    content = <p>Access granted</p>;
  }

  return <div>{content}</div>;
};
