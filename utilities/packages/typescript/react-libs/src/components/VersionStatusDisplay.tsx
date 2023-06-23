import RestoreIcon from "@mui/icons-material/Restore";
import { Button, IconButton, Stack } from "@mui/material";

const defaultStackDirection = "column";
const defaultContolButtonSpacing = 1;

export interface VersionStatusDisplayProps {
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

export const VersionStatusDisplay = (props: VersionStatusDisplayProps) => {
    /**
    Component: VersionStatusComponent

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
            spacing={0.5}
            alignItems="center"
            justifyContent={"center"}
        >
            <p>
                <b>
                    {props.isLatest
                        ? "Latest"
                        : props.historyId !== undefined
                        ? `v${props.historyId}`
                        : "Unknown"}{" "}
                </b>
            </p>
            {showRequestChange && (
                <IconButton onClick={props.onRequestCheckout}>
                    <RestoreIcon fontSize="medium" />
                </IconButton>
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
                            Revert to version
                        </Button>
                    )}
                    {showReturnToLatest && (
                        <Button
                            onClick={props.onRequestReturnToLatest}
                            variant="outlined"
                        >
                            Return to latest
                        </Button>
                    )}
                </Stack>
            )}
        </Stack>
    );
};
