import { Snackbar, SnackbarContent, Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useEffect } from "react";

// Custom styles for SnackbarContent based on color
const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    success: {
      backgroundColor: "green",
    },
    inProgress: {
      backgroundColor: "lightslategray",
    },
  }),
);

export type PopupColors = "success" | "inProgress";
interface BriefPopupProps {
  message: string;
  open: boolean;
  handleClose: () => void;
  color: PopupColors;
}

export default function BriefPopup(props: BriefPopupProps) {
  const { message, open, handleClose, color } = props;
  const classes = useStyles();

  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => {
        props.handleClose();
      }, 3000);
      return () => {
        // clean up
        clearTimeout(timer);
      };
    }
  }, [props.open]);

  return (
    <Snackbar
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "left",
      }}
      open={open}
      autoHideDuration={null} // Auto hide after 3 seconds
      onClose={handleClose}
    >
      <SnackbarContent
        message={message}
        className={classes[color]} // Apply custom style based on color
      ></SnackbarContent>
    </Snackbar>
  );
}
