import { Alert, AlertTitle, Collapse } from "@mui/material";

interface SuccessPopupProps {
  title: string;
  message: string;
  // It's state is controlled by a parent
  open: boolean;
}

export const SuccessPopup = (props: SuccessPopupProps) => {
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
};
