import { Grid } from "@mui/material";
import React from "react";
import {
  UseMetadataHistorySelectorOutput,
  UseRevertDialogOutput,
} from "../hooks";
import { MetadataHistoryStatusDisplay } from "./MetadataHistoryStatusDisplay";

interface MetadataHistoryProps {
  // Should be hidden if there is a history error
  hide: boolean;
  // If entity is locked
  locked: boolean;
  // Write permission
  writeAccessGranted: boolean;
  // If current metadata version is the latest one
  isLatest: boolean;
  // Latest metadata history id
  latestId?: number;
  // Hook controls for metadata version and revert
  versionControls: UseMetadataHistorySelectorOutput;
  revertControls: UseRevertDialogOutput;
}

export const MetadataHistory = (props: MetadataHistoryProps) => {
  /**
     * Component: MetadataHistory

     For showing metadata history version with revert functionalities
     *
     */

  return (
    <React.Fragment>
      <Grid
        container
        alignItems={"center"}
        justifyContent={"flex-start"}
        spacing={2}
        padding={0}
      >
        {/* Title */}

        <Grid item xs={3}>
          <h2>Metadata History</h2>
        </Grid>

        {/* Metadata history content */}

        <Grid item>
          <MetadataHistoryStatusDisplay
            // Should be hidden if there is a history error
            hide={props.hide}
            locked={props.locked}
            writePermission={props.writeAccessGranted}
            historyId={props.versionControls.state?.historyId}
            isLatest={props.isLatest ?? true}
            onRequestCheckout={() => {
              if (
                props.versionControls.controls?.startSelection !== undefined
              ) {
                props.versionControls.controls.startSelection();
              }
            }}
            onRequestRevert={() => {
              if (props.revertControls.startRevert !== undefined) {
                props.revertControls.startRevert();
              }
            }}
            onRequestReturnToLatest={() => {
              if (props.versionControls.controls?.manuallySetId !== undefined) {
                if (props.latestId !== undefined) {
                  props.versionControls.controls.manuallySetId(props.latestId);
                }
              }
            }}
            controlButtonStackOrientation="row"
          />
        </Grid>

        {/* Description */}

        <Grid item xs={12}>
          Click the icon above to inspect the history of this item's metadata.
        </Grid>
      </Grid>
    </React.Fragment>
  );
};
