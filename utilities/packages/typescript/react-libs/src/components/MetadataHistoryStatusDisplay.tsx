import RestoreIcon from "@mui/icons-material/Restore";
import { Button, IconButton, Stack, Tooltip, Typography } from "@mui/material";

const defaultStackDirection = "column";
const defaultContolButtonSpacing = 1;

export interface MetadataHistoryStatusDisplayProps {
  // If we are in a historical version else undefined
  historyId?: number;
  // Regardless of if ID is present - we should still know if latest or not
  isLatest: boolean;

  // Is the item locked?
  locked: boolean;

  // Does the user have write permission?
  writePermission: boolean;

  // Override to hide the component
  hide?: boolean;

  // Behaviours
  onRequestCheckout: () => void;
  onRequestRevert: () => void;
  onRequestReturnToLatest: () => void;

  // Optional layout config

  // Control button stack orientation
  controlButtonStackOrientation?: "column" | "row" | undefined;
  controlButtonSpacing?: number;
}

export const MetadataHistoryStatusDisplay = (
  props: MetadataHistoryStatusDisplayProps,
) => {
  /**
    Component: MetadataHistoryStatusDisplay

    Displays the currently selected historical version of the item and some
    basic controls where suitable. 

    This does not handle the actions of those controls - just visualises the
    hooks.

    NOTE will never show revert option if locked

    NOTE there is an invalid state in these props when isLatest = False but
    history ID is not supplied. No error is thrown but no actions are allowed.
    */

  // Default vals

  const controlButtonStackOrientation =
    props.controlButtonStackOrientation ?? defaultStackDirection;
  const controlButtonSpacing =
    props.controlButtonSpacing !== undefined
      ? props.controlButtonSpacing
      : defaultContolButtonSpacing;

  const staleState = props.historyId === undefined && !props.isLatest;

  // Currently we always allow show request change
  const showRequestChange = !staleState;

  // Only show request revert if not latest
  const showReturnToLatest = !props.isLatest && !staleState;
  const showRequestRevert = showReturnToLatest && props.writePermission;

  // Is the revert op actually enabled
  const revertOpEnabled = !props.locked;

  if (props.hide) {
    return null;
  }

  return (
    <Stack
      direction="row"
      spacing={1}
      alignItems="center"
      justifyContent={"center"}
    >
      <Typography variant="body1">
        <strong>
          {props.isLatest
            ? "Latest"
            : props.historyId !== undefined
              ? `Metadata v${props.historyId}`
              : "Unknown"}{" "}
        </strong>
      </Typography>
      {showRequestChange && (
        <Tooltip title="Click to manage the metadata history">
          <IconButton onClick={props.onRequestCheckout}>
            <RestoreIcon fontSize="medium" />
          </IconButton>
        </Tooltip>
      )}
      {(showRequestRevert || showReturnToLatest) && (
        <Stack
          direction={controlButtonStackOrientation}
          spacing={controlButtonSpacing}
        >
          {showRequestRevert && (
            <Button
              disabled={!revertOpEnabled}
              onClick={props.onRequestRevert}
              variant="outlined"
            >
              Revert
            </Button>
          )}
          {showReturnToLatest && (
            <Button onClick={props.onRequestReturnToLatest} variant="outlined">
              Return to latest
            </Button>
          )}
        </Stack>
      )}
    </Stack>
  );
};
