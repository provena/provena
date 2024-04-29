import { Alert, Button, Divider, Grid, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { useState } from "react";
import { useAccessCheck } from "../hooks";
import ProvGraph from "./ProvGraph";
import {
  LegendInformation,
  LegendInformationProps,
} from "./LegendItemInformation";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    bodyPanelContainer: {
      margin: theme.spacing(0),
    },
    recordInfoPanel: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "start",
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(4),
      borderRadius: 5,
    },
    accessAPIContainer: {
      paddingBottom: theme.spacing(1),
    },
    accessAPIPanel: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "start",
      alignItems: "left",
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(4),
      borderRadius: 5,
    },
    hidden: {
      display: "none",
    },
    alert: {
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      paddingBottom: theme.spacing(1),
      paddingTop: theme.spacing(1),
      width: "100%",
    },
  }),
);

interface LegendProps {
  colour: string;
  acronym: string;
  name: object;
}

const LegendItem = (props: LegendProps) => {
  return (
    <Grid
      container
      item
      xs={12}
      sm={6}
      sx={{
        display: "flex",
        textAlign: "start",
        justifyContent: "space-around",
        flexDirection: "row",
        marginBottom: "12px",
      }}
    >
      <Grid container item xs={2} sm={1} sx={{ justifyContent: "end" }}>
        <Grid
          item
          sx={{
            backgroundColor: props.colour,
            width: "25px",
            height: "25px",
            borderRadius: "13px",
          }}
        ></Grid>
      </Grid>
      <Grid
        container
        item
        xs={2}
        sm={1}
        sx={{ justifyContent: "center", paddingTop: "4px" }}
      >
        <Typography variant="caption">{props.acronym}</Typography>
      </Grid>
      <Grid
        container
        item
        xs={8}
        sm={4}
        sx={{ justifyContent: "start", paddingTop: "4px" }}
      >
        <Typography variant="caption">&nbsp;{props.name}</Typography>
      </Grid>
    </Grid>
  );
};

interface ProvGraphTabViewProps {
  // Root id
  rootID: string;
}

export const ProvGraphTabView = observer((props: ProvGraphTabViewProps) => {
  /**
    Component: ProvGraphTabView

    Renders ProvGraph with horizontal Legend for showing as a component in tabs.

    */

  const classes = useStyles();

  // Use auth
  const readCheck = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "READ",
  });

  const [rootId, setRootId] = useState<string>(props.rootID);

  // Graph state
  const [graphExpanded, setGraphExpanded] = useState<boolean>(false);

  const accessErrorOccurred = readCheck.error;
  const readAccessDeniedGlobal = !readCheck.fallbackGranted;

  return (
    <Grid container>
      <Grid
        id="rootEntityPanel"
        container
        item
        xs={12}
        className={graphExpanded === false ? "" : classes.hidden}
      >
        <Grid container item xs={12} className={classes.recordInfoPanel}>
          <Grid container item xs={12} className={classes.bodyPanelContainer}>
            {readAccessDeniedGlobal && (
              <Alert
                className={classes.alert}
                severity="error"
                action={
                  <Button variant="outlined" href="/profile">
                    Request Access
                  </Button>
                }
              >
                You do not have sufficient registry store permissions to view
                entity record details.
              </Alert>
            )}
            {accessErrorOccurred && (
              <Alert className={classes.alert} severity="error">
                An error occurred while determining access error:{" "}
                {readCheck.errorMessage ??
                  "Unknown - check console and contact us for help."}
              </Alert>
            )}

            <Grid container item xs={12}>
              <Grid container item xs={12}>
                <Grid
                  item
                  xs={12}
                  sx={{
                    display: "flex",
                    flexWrap: "wrap",
                    flexDirection: "row",
                    padding: "12px",
                    border: "1px dotted black",
                    borderRadius: "5px",
                  }}
                >
                  <Typography variant="h6">Legend</Typography>
                  <Divider
                    sx={{
                      width: "100%",
                      marginBottom: "12px",
                    }}
                  />
                  {LegendInformation.map((legend: LegendInformationProps) => (
                    <LegendItem
                      colour={legend.colour}
                      acronym={legend.acronym}
                      name={
                        <span>
                          <a href={legend.href} target="_blank">
                            {legend.name}
                          </a>
                        </span>
                      }
                    />
                  ))}
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      <Grid id="graphPanel" container item xs={12}>
        <Grid container item xs={12} className={classes.accessAPIContainer}>
          <Grid container item xs={12} className={classes.accessAPIPanel}>
            {
              // Show the prov graph as long as read access is available -
              //even if there is an error loading the root node we may still explore e.g. 401 error
            }
            {!readAccessDeniedGlobal && (
              <ProvGraph
                rootId={rootId!}
                setRootId={setRootId!}
                toggleExpanded={() => {
                  setGraphExpanded((old) => !old);
                }}
                expanded={graphExpanded}
              />
            )}
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
});
